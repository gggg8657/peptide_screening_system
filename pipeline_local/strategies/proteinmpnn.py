"""ProteinMPNN 기반 시퀀스 변이 생성 전략.

Phase 3: peptide_only 모드와 receptor_context 모드를 지원.

- peptide_only: SST-14 시퀀스만 ligandmpnn에 입력 (receptor context 없음)
  → 임시 extended-backbone PDB를 자동 생성해 입력
- receptor_context: complex_pdb 경로가 있을 때만 활성화. 없으면
  validate_env()가 (False, 에러 메시지)를 반환 → orchestrator가 처리.

pharmacophore guard: 생성된 모든 시퀀스에 대해 fixed_positions 보존 여부를
재검증하고 위반 시 해당 변이체를 제거.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from pipeline_local.schemas.io_schemas import Step03bOutput, VariantEntry
from pipeline_local.strategies.blosum import (
    DEFAULT_REFERENCE_PEPTIDE_SEQUENCE,
    hydrophobicity_check,
    validate_constraints,
)

logger = logging.getLogger(__name__)

# 1-letter → 3-letter 아미노산 코드 매핑
_AA1TO3: Dict[str, str] = {
    "A": "ALA", "C": "CYS", "D": "ASP", "E": "GLU", "F": "PHE",
    "G": "GLY", "H": "HIS", "I": "ILE", "K": "LYS", "L": "LEU",
    "M": "MET", "N": "ASN", "P": "PRO", "Q": "GLN", "R": "ARG",
    "S": "SER", "T": "THR", "V": "VAL", "W": "TRP", "Y": "TYR",
}

# 표준 20종 아미노산 집합 (검증용)
_STANDARD_AA: frozenset[str] = frozenset(_AA1TO3.keys())

# proteinmpnn conda env 이름
_PROTEINMPNN_ENV = "proteinmpnn"


def _make_extended_backbone_pdb(sequence: str, chain: str = "A") -> str:
    """시퀀스로부터 extended conformation backbone PDB 내용을 생성한다.

    N-CA-C-O 4원자 backbone을 단순 planar extended 형태로 배치.
    ligandmpnn 파싱에 필요한 최소 구조를 충족.

    Args:
        sequence: 1-letter 아미노산 시퀀스
        chain:    체인 ID (기본값 "A")

    Returns:
        PDB 형식 문자열
    """
    lines: List[str] = []
    atom_idx = 1
    for i, aa in enumerate(sequence):
        resnum = i + 1
        res3 = _AA1TO3.get(aa.upper(), "GLY")
        x_base = float(i) * 3.8
        # N
        lines.append(
            f"ATOM  {atom_idx:5d}  N   {res3} {chain}{resnum:4d}    "
            f"{x_base:8.3f}   0.000   0.000  1.00  0.00           N  "
        )
        atom_idx += 1
        # CA
        lines.append(
            f"ATOM  {atom_idx:5d}  CA  {res3} {chain}{resnum:4d}    "
            f"{x_base + 1.46:8.3f}   1.200   0.000  1.00  0.00           C  "
        )
        atom_idx += 1
        # C
        lines.append(
            f"ATOM  {atom_idx:5d}  C   {res3} {chain}{resnum:4d}    "
            f"{x_base + 2.98:8.3f}   0.000   0.000  1.00  0.00           C  "
        )
        atom_idx += 1
        # O
        lines.append(
            f"ATOM  {atom_idx:5d}  O   {res3} {chain}{resnum:4d}    "
            f"{x_base + 3.28:8.3f}  -1.200   0.000  1.00  0.00           O  "
        )
        atom_idx += 1
    lines.append("END")
    return "\n".join(lines)


def _fixed_positions_to_ligandmpnn_str(
    fixed_positions: Dict[int, str],
    chain: str = "A",
) -> str:
    """fixed_positions 딕셔너리를 ligandmpnn --fixed_residues 형식으로 변환.

    예: {3: "C", 7: "F"} → "A3 A7"

    Args:
        fixed_positions: 1-indexed 위치 → 아미노산 매핑
        chain:           체인 ID

    Returns:
        "A3 A7 A8 A9 A10 A14" 형식 문자열
    """
    return " ".join(
        f"{chain}{pos}" for pos in sorted(fixed_positions.keys())
    )


def _parse_fasta_sequences(fasta_path: str) -> List[Tuple[str, str]]:
    """ligandmpnn 출력 FASTA에서 (헤더, 시퀀스) 쌍 목록을 파싱.

    첫 번째 엔트리(native/seed)는 제외하고 생성된 시퀀스만 반환.

    Args:
        fasta_path: FASTA 파일 경로

    Returns:
        (header, sequence) 튜플 목록 (seed 제외)
    """
    pairs: List[Tuple[str, str]] = []
    current_header: Optional[str] = None
    current_seq: List[str] = []

    with open(fasta_path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if current_header is not None:
                    pairs.append((current_header, "".join(current_seq)))
                current_header = line[1:]
                current_seq = []
            else:
                current_seq.append(line)
    if current_header is not None:
        pairs.append((current_header, "".join(current_seq)))

    # 첫 번째 엔트리(seed/native)는 id= 필드가 없음 → 생성 시퀀스만 필터
    return [(h, s) for h, s in pairs if "id=" in h]


def _parse_confidence(header: str) -> float:
    """FASTA 헤더에서 overall_confidence 값을 추출.

    Args:
        header: FASTA 헤더 문자열

    Returns:
        overall_confidence float 값, 파싱 실패 시 0.0
    """
    m = re.search(r"overall_confidence=([\d.]+)", header)
    if m:
        return float(m.group(1))
    return 0.0


def _parse_seq_id(header: str) -> Optional[int]:
    """FASTA 헤더에서 id= 값을 추출.

    Args:
        header: FASTA 헤더 문자열

    Returns:
        id 정수 값, 파싱 실패 시 None
    """
    m = re.search(r"\bid=(\d+)", header)
    if m:
        return int(m.group(1))
    return None


class ProteinMPNNStrategy:
    """ligandmpnn을 통한 ProteinMPNN 시퀀스 변이 생성 전략.

    두 가지 mode를 지원:
    - peptide_only: SST-14 시퀀스만 입력, extended backbone PDB 자동 생성
    - receptor_context: complex_pdb 경로 필수, 없으면 validate_env() 실패
    """

    name = "proteinmpnn"

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def validate_env(self, config: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """환경 유효성 검사.

        검사 항목:
        1. proteinmpnn conda env 존재 여부
        2. ligandmpnn 패키지 설치 여부
        3. receptor_context 모드 시 complex_pdb 경로 유효성

        Args:
            config: generate()와 동일한 config dict (mode 검사용, 없으면 생략)

        Returns:
            (True, None) 또는 (False, 에러 메시지)
        """
        # 1. conda env 존재 확인
        env_ok, env_err = self._check_conda_env(_PROTEINMPNN_ENV)
        if not env_ok:
            return False, env_err

        # 2. ligandmpnn 설치 확인
        pkg_ok, pkg_err = self._check_ligandmpnn_installed()
        if not pkg_ok:
            return False, pkg_err

        # 3. receptor_context 모드: complex_pdb 경로 유효성
        if config is not None:
            ab_cfg = config.get("approach_b", config)
            opts = ab_cfg.get("proteinmpnn_opts", {})
            mode = str(opts.get("mode", "peptide_only"))
            if mode == "receptor_context":
                complex_pdb = opts.get("complex_pdb")
                if not complex_pdb:
                    return (
                        False,
                        "receptor_context 모드에는 proteinmpnn_opts.complex_pdb 경로가 필요합니다. "
                        "complex_pdb가 없으면 mode='peptide_only'로 변경하거나 Boltz로 complex를 먼저 생성하세요.",
                    )
                if not os.path.isfile(str(complex_pdb)):
                    return (
                        False,
                        f"receptor_context 모드: complex_pdb 파일이 존재하지 않습니다: {complex_pdb}",
                    )

        return True, None

    def generate(self, config: dict) -> Step03bOutput:
        """config에 따라 ProteinMPNN 변이체를 생성한다.

        Args:
            config: approach_b 섹션을 포함하는 파이프라인 설정 dict.
                필수 키:
                    approach_b.seed_sequence (기본값: SST-14)
                    approach_b.fixed_positions
                선택 키:
                    approach_b.proteinmpnn_opts.mode ("peptide_only" | "receptor_context")
                    approach_b.proteinmpnn_opts.complex_pdb
                    approach_b.proteinmpnn_opts.num_seq_per_target (기본값: 100)
                    approach_b.proteinmpnn_opts.sampling_temperature (기본값: 0.1)
                    approach_b.proteinmpnn_opts.device (기본값: "cuda:0")
                    approach_b.max_variants (기본값: 100)
                    approach_b.hydrophobicity_max_delta (기본값: 2.0)

        Returns:
            Step03bOutput (pharmacophore 가드 통과 변이체만 포함)

        Raises:
            RuntimeError: validate_env 실패 또는 ligandmpnn subprocess 오류
        """
        ab_cfg = config.get("approach_b", config)
        ref_cfg = config.get("reference_peptide", {})

        seed = str(ab_cfg.get(
            "seed_sequence",
            ref_cfg.get("sequence", DEFAULT_REFERENCE_PEPTIDE_SEQUENCE),
        ))

        fixed_raw = ab_cfg.get(
            "fixed_positions",
            {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"},
        )
        fixed_positions: Dict[int, str] = {int(k): str(v) for k, v in fixed_raw.items()}

        max_variants = int(ab_cfg.get("max_variants", 100))
        max_hydro_delta = float(ab_cfg.get("hydrophobicity_max_delta", 2.0))

        opts = ab_cfg.get("proteinmpnn_opts", {})
        mode = str(opts.get("mode", "peptide_only"))
        complex_pdb: Optional[str] = opts.get("complex_pdb") or None
        num_seq = int(opts.get("num_seq_per_target", 100))
        temperature = float(opts.get("sampling_temperature", 0.1))
        device = str(opts.get("device", "cuda:0"))

        # 환경 검사 (mode 포함)
        ok, err = self.validate_env(config)
        if not ok:
            raise RuntimeError(f"[ProteinMPNNStrategy] 환경 검사 실패: {err}")

        logger.info(
            "[Step03b] ProteinMPNN 시작: mode=%s, seed=%s, num_seq=%d, temperature=%.2f",
            mode, seed, num_seq, temperature,
        )

        # 임시 작업 디렉토리
        workdir = tempfile.mkdtemp(prefix="pmpnn_gen_")
        try:
            pdb_path, peptide_chain = self._prepare_pdb(
                mode=mode,
                seed=seed,
                complex_pdb=complex_pdb,
                workdir=workdir,
            )
            out_dir = os.path.join(workdir, "output")
            os.makedirs(out_dir, exist_ok=True)

            fixed_str = _fixed_positions_to_ligandmpnn_str(fixed_positions, chain=peptide_chain)

            self._run_ligandmpnn(
                pdb_path=pdb_path,
                out_dir=out_dir,
                fixed_str=fixed_str,
                num_seq=num_seq,
                temperature=temperature,
                device=device,
                peptide_chain=peptide_chain if mode == "receptor_context" else None,
            )

            raw_seqs = self._collect_sequences(out_dir)
            logger.info(
                "[Step03b] ProteinMPNN ligandmpnn 완료: raw %d 시퀀스 수집", len(raw_seqs)
            )

            variants = self._apply_pharmacophore_guard(
                raw_seqs=raw_seqs,
                seed=seed,
                fixed_positions=fixed_positions,
                max_variants=max_variants,
                max_hydro_delta=max_hydro_delta,
            )
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

        logger.info(
            "[Step03b] ProteinMPNN 최종 변이체 수: %d / %d (pharmacophore 통과)",
            len(variants), num_seq,
        )
        return Step03bOutput(
            variants=variants,
            seed_sequence=seed,
            fixed_positions=fixed_positions,
            total_generated=len(variants),
            strategy="approach_b",
        )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _check_conda_env(env_name: str) -> Tuple[bool, Optional[str]]:
        """conda env 존재 여부를 확인한다."""
        try:
            result = subprocess.run(
                ["conda", "env", "list"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if env_name in result.stdout:
                return True, None
            return (
                False,
                f"conda env '{env_name}' 가 존재하지 않습니다. "
                f"'conda create -n {env_name}' 로 환경을 먼저 생성하세요.",
            )
        except FileNotFoundError:
            return False, "conda 명령을 찾을 수 없습니다. conda가 설치되어 있는지 확인하세요."
        except subprocess.TimeoutExpired:
            return False, "conda env list 타임아웃 (30s)"

    @staticmethod
    def _check_ligandmpnn_installed() -> Tuple[bool, Optional[str]]:
        """proteinmpnn env 내부에서 ligandmpnn import 가능 여부를 확인한다."""
        try:
            result = subprocess.run(
                [
                    "conda", "run", "-n", _PROTEINMPNN_ENV,
                    "python", "-c", "import ligandmpnn; print('ok')",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and "ok" in result.stdout:
                return True, None
            return (
                False,
                f"ligandmpnn 패키지가 설치되어 있지 않습니다. "
                f"'conda run -n {_PROTEINMPNN_ENV} pip install ligandmpnn' 로 설치하세요.\n"
                f"stderr: {result.stderr[:200]}",
            )
        except subprocess.TimeoutExpired:
            return False, "ligandmpnn import 확인 타임아웃 (30s)"

    @staticmethod
    def _prepare_pdb(
        mode: str,
        seed: str,
        complex_pdb: Optional[str],
        workdir: str,
    ) -> Tuple[str, str]:
        """mode에 따라 입력 PDB 경로와 peptide chain ID를 반환한다.

        peptide_only: extended backbone PDB를 workdir에 생성 후 경로 반환
        receptor_context: complex_pdb 경로를 그대로 반환 (chain B 가정)

        Returns:
            (pdb_path, peptide_chain_id)
        """
        if mode == "receptor_context":
            if complex_pdb is None:
                raise RuntimeError(
                    "receptor_context 모드인데 complex_pdb가 None입니다. "
                    "validate_env()를 먼저 호출하세요."
                )
            return str(complex_pdb), "B"

        # peptide_only: extended backbone 자동 생성
        pdb_content = _make_extended_backbone_pdb(seed, chain="A")
        pdb_path = os.path.join(workdir, "peptide.pdb")
        with open(pdb_path, "w") as f:
            f.write(pdb_content)
        return pdb_path, "A"

    @staticmethod
    def _run_ligandmpnn(
        pdb_path: str,
        out_dir: str,
        fixed_str: str,
        num_seq: int,
        temperature: float,
        device: str,
        peptide_chain: Optional[str],
    ) -> None:
        """ligandmpnn subprocess를 실행한다.

        Args:
            pdb_path:       입력 PDB 경로
            out_dir:        출력 디렉토리
            fixed_str:      "--fixed_residues" 값 (예: "A3 A7 A8")
            num_seq:        생성 시퀀스 수 (number_of_batches)
            temperature:    sampling temperature
            device:         CUDA/CPU 디바이스 (예: "cuda:0", "cpu")
            peptide_chain:  receptor_context 모드에서 설계할 체인 ID (None → 전체)
        """
        cmd: List[str] = [
            "conda", "run", "-n", _PROTEINMPNN_ENV,
            "python", "-m", "ligandmpnn.run",
            "--model_type", "protein_mpnn",
            "--pdb_path", pdb_path,
            "--out_folder", out_dir,
            "--number_of_batches", str(num_seq),
            "--batch_size", "1",
            "--temperature", str(temperature),
            "--verbose", "0",
        ]

        if fixed_str:
            cmd += ["--fixed_residues", fixed_str]

        # receptor_context 모드: 특정 체인만 redesign
        if peptide_chain:
            cmd += ["--chains_to_design", peptide_chain]

        # CUDA_VISIBLE_DEVICES 설정 (device="cuda:N" → N)
        env = os.environ.copy()
        if device.startswith("cuda:"):
            gpu_id = device.split(":", 1)[1]
            env["CUDA_VISIBLE_DEVICES"] = gpu_id
        elif device == "cpu":
            env["CUDA_VISIBLE_DEVICES"] = ""

        logger.debug("[Step03b] ligandmpnn cmd: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"[Step03b] ligandmpnn subprocess 실패 (returncode={result.returncode}).\n"
                f"STDERR: {result.stderr[-1000:]}"
            )

    @staticmethod
    def _collect_sequences(out_dir: str) -> List[Tuple[str, str, float]]:
        """out_dir/seqs/ 하위 FASTA 파일을 읽어 (header, sequence, confidence) 목록 반환.

        Args:
            out_dir: ligandmpnn 출력 루트 디렉토리

        Returns:
            (header, sequence, confidence) 튜플 목록
        """
        seqs_dir = os.path.join(out_dir, "seqs")
        if not os.path.isdir(seqs_dir):
            return []

        results: List[Tuple[str, str, float]] = []
        for fa_file in sorted(os.listdir(seqs_dir)):
            if not fa_file.endswith(".fa"):
                continue
            pairs = _parse_fasta_sequences(os.path.join(seqs_dir, fa_file))
            for header, seq in pairs:
                conf = _parse_confidence(header)
                results.append((header, seq, conf))

        # confidence 내림차순 정렬
        results.sort(key=lambda x: -x[2])
        return results

    @staticmethod
    def _apply_pharmacophore_guard(
        raw_seqs: List[Tuple[str, str, float]],
        seed: str,
        fixed_positions: Dict[int, str],
        max_variants: int,
        max_hydro_delta: float,
    ) -> List[VariantEntry]:
        """pharmacophore 가드 적용: fixed_positions 위반 및 소수성 극단 시퀀스 제거.

        Args:
            raw_seqs:        (header, sequence, confidence) 목록
            seed:            원본 시퀀스
            fixed_positions: 고정 위치 제약
            max_variants:    최대 반환 변이체 수
            max_hydro_delta: 소수성 최대 허용 변화량

        Returns:
            VariantEntry 목록 (pharmacophore 통과 + 중복 제거 + max_variants 제한)
        """
        seen: set[str] = set()
        variants: List[VariantEntry] = []

        for header, seq, confidence in raw_seqs:
            if len(variants) >= max_variants:
                break

            # 길이 일치 확인
            if len(seq) != len(seed):
                logger.debug(
                    "[Step03b][guard] 길이 불일치 제거: '%s' (len=%d, seed=%d)",
                    seq, len(seq), len(seed),
                )
                continue

            # 표준 아미노산만 허용
            if not all(aa in _STANDARD_AA for aa in seq.upper()):
                logger.debug("[Step03b][guard] 비표준 잔기 제거: %s", seq)
                continue

            seq_upper = seq.upper()

            # 중복 제거
            if seq_upper in seen:
                continue
            seen.add(seq_upper)

            # seed와 동일한 시퀀스 제거
            if seq_upper == seed.upper():
                continue

            # pharmacophore: fixed_positions 보존 검증
            if not validate_constraints(seq_upper, fixed_positions):
                logger.debug(
                    "[Step03b][guard] pharmacophore 위반 제거: %s", seq_upper
                )
                continue

            # 소수성 가드
            if not hydrophobicity_check(seq_upper, seed, max_hydro_delta):
                logger.debug(
                    "[Step03b][guard] 소수성 위반 제거: %s", seq_upper
                )
                continue

            # 변이 목록 계산
            mutations: List[str] = []
            for i, (orig, mut) in enumerate(zip(seed.upper(), seq_upper), start=1):
                if orig != mut:
                    mutations.append(f"{orig}{i}{mut}")

            variants.append(VariantEntry(
                variant_id="",  # 아래에서 일괄 설정
                sequence=seq_upper,
                parent_sequence=seed,
                mutations=mutations,
                n_mutations=len(mutations),
                blosum_total_score=0,  # ProteinMPNN은 BLOSUM 점수 없음
                source="proteinmpnn",
            ))

        # variant_id 순번 부여
        for idx, v in enumerate(variants, start=1):
            v.variant_id = f"var_{idx:03d}"

        return variants
