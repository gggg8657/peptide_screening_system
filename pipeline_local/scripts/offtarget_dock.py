#!/usr/bin/env python3
"""
offtarget_dock.py — Boltz-2 + AlphaFoldDB MSA off-target docking subprocess script
====================================================================================
수용체 구조(CIF/PDB)와 펩타이드 서열을 입력으로 받아 Boltz-2로 구조 예측 후
iPTM 기반 결합 친화도 프록시를 stdout JSON으로 출력한다.

KAERI 내부망 우회:
    ColabFold MSA 서버(api.colabfold.com) 차단 환경에서는 AlphaFoldDB MSA를
    사전 다운로드하여 사용한다.
    상세: docs/boltz2_offline_workaround.md

Usage:
    conda run -n boltz python offtarget_dock.py \\
        --receptor /path/to/receptor.cif \\
        --sequence AGCKNFFWKTFTSC \\
        --nstruct 1 \\
        --output-dir /path/to/output

Output (stdout, 마지막 줄):
    {
      "ddg":        -95.4,      # iPTM 기반 프록시 (-100 * iptm), 하위 호환 유지
      "iptm":       0.954,      # interface predicted TM-score
      "ptm":        0.869,      # predicted TM-score
      "confidence": 0.859,      # Boltz confidence_score
      "best_pdb":   "...",      # 최적 구조 PDB 경로 (output-dir 지정 시)
      "engine":     "boltz-2"   # 엔진 식별자
    }

Error (stdout):
    {"error": "메시지"}

GPU 선택:
    환경 변수 OFFTARGET_DOCK_CUDA_DEVICE 로 GPU 지정 (기본 "0")

PyRosetta 레거시:
    기존 FlexPepDock 기반 구현은 offtarget_dock_pyrosetta_legacy.py 에 보존됨.
    부적합 판정 근거: docs/selectivity_demo_20260511/report_final.html
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SSTR 수용체 UniProt 매핑 (KAERI 내부망 검증 완료)
# ---------------------------------------------------------------------------

SSTR_UNIPROT: Dict[str, str] = {
    "SSTR1": "P30872",
    "SSTR2": "P30874",
    "SSTR3": "P32745",
    "SSTR4": "P31391",
    "SSTR5": "P35346",
}

# 각 SSTR 서열의 N-말단 특징 서열 (UniProt reviewed isoform 1 기준)
# N-말단이 구조 파일에 없을 경우를 대비해 내부 서열도 포함
_SSTR_SIGNATURES: Dict[str, List[str]] = {
    # 주의: SSTR1/SSTR4 공유 모티프 "VILRYAKMKTA"는 서브타입 오매칭을 유발하므로 제거됨.
    # 각 서브타입의 고유 시그니처(TM3 N-말단 또는 N-터미너스)만 유지.
    "SSTR1": ["MFPNGTASSPS", "YSVVCLVGLCG"],
    "SSTR2": ["MDMADEPLNGS", "YFVVCIIGLCG", "VILRYAKMKTI"],
    "SSTR3": ["MDMLHPSSVST", "YLVCVVGLLGN", "VVLRHTASPSVT"],
    "SSTR4": ["MSAPSTLPPGG", "YALVCLVGLVG"],
    "SSTR5": ["MEPLFPASTP", "YLLVCAAGLGG", "VVLRFATVTNI"],
}

# AlphaFoldDB MSA 캐시 디렉토리 (기본)
_DEFAULT_MSA_CACHE: Path = Path.home() / ".cache" / "boltz_msa"

# 3문자 → 1문자 아미노산 코드
_THREE_TO_ONE: Dict[str, str] = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "SEC": "U", "PYL": "O",
}


# ---------------------------------------------------------------------------
# PDB / CIF 서열 추출
# ---------------------------------------------------------------------------

def _extract_sequence_from_pdb(pdb_path: str) -> str:
    """PDB/CIF 파일에서 수용체 주요 체인의 아미노산 서열을 추출한다.

    전략:
        - PDB 형식: ATOM 레코드의 CA 원자 수집 → 가장 긴 체인 선택
        - CIF 형식: _atom_site 루프에서 ATOM 그룹, CA 원자 수집

    Args:
        pdb_path: 구조 파일 경로 (.pdb 또는 .cif)

    Returns:
        1문자 아미노산 서열 (가장 긴 체인)

    Raises:
        ValueError: CA 원자를 찾을 수 없거나 서열이 비어 있는 경우
    """
    suffix = Path(pdb_path).suffix.lower()
    if suffix in (".cif", ".mmcif"):
        return _extract_from_cif(pdb_path)
    return _extract_from_pdb_format(pdb_path)


def _extract_from_pdb_format(pdb_path: str) -> str:
    """표준 PDB 형식 ATOM 레코드에서 서열 추출."""
    # {chain_id: [(resseq, aa_one_letter), ...]}
    chain_res: Dict[str, List[Tuple[int, str]]] = {}
    seen: Dict[str, set] = {}

    with open(pdb_path, "r", errors="replace") as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            if len(line) < 27:
                continue
            atom_name = line[12:16].strip()
            if atom_name != "CA":
                continue
            resname = line[17:20].strip()
            chain_id = line[21]
            try:
                resseq = int(line[22:26].strip())
            except ValueError:
                continue
            aa = _THREE_TO_ONE.get(resname)
            if aa is None:
                continue
            key = (resseq, line[26].strip())  # insertion code 포함
            if key not in seen.setdefault(chain_id, set()):
                seen[chain_id].add(key)
                chain_res.setdefault(chain_id, []).append((resseq, aa))

    if not chain_res:
        raise ValueError(f"PDB에서 CA 원자를 찾을 수 없습니다: {pdb_path}")

    return _select_receptor_sequence(chain_res, pdb_path, "PDB")


def _extract_from_cif(cif_path: str) -> str:
    """mmCIF _atom_site 루프에서 서열 추출."""
    chain_res: Dict[str, List[Tuple[int, str]]] = {}
    seen: Dict[str, set] = {}

    col_map: Dict[str, int] = {}
    in_loop = False
    col_idx = 0

    with open(cif_path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip()

            # _atom_site 컬럼 인덱스 수집
            if line.startswith("_atom_site."):
                field = line.split(".", 1)[1].strip()
                col_map[field] = col_idx
                col_idx += 1
                in_loop = True
                continue

            if in_loop:
                # 새 카테고리 혹은 섹션 종료
                if line.startswith("_") or line.startswith("#") or not line:
                    if col_map:
                        in_loop = False
                        col_idx = 0
                        col_map = {}
                    continue

                parts = line.split()
                if not parts:
                    continue
                # 필수 컬럼 체크
                needed = {"group_PDB", "label_atom_id", "label_comp_id",
                          "label_asym_id", "label_seq_id"}
                if not needed.issubset(col_map):
                    continue
                if len(parts) <= max(col_map[k] for k in needed):
                    continue

                if parts[col_map["group_PDB"]] != "ATOM":
                    continue
                if parts[col_map["label_atom_id"]] != "CA":
                    continue

                resname = parts[col_map["label_comp_id"]]
                chain_id = parts[col_map["label_asym_id"]]
                try:
                    resseq = int(parts[col_map["label_seq_id"]])
                except ValueError:
                    continue
                aa = _THREE_TO_ONE.get(resname)
                if aa is None:
                    continue
                if resseq not in seen.setdefault(chain_id, set()):
                    seen[chain_id].add(resseq)
                    chain_res.setdefault(chain_id, []).append((resseq, aa))

    if not chain_res:
        raise ValueError(f"CIF에서 CA 원자를 찾을 수 없습니다: {cif_path}")

    return _select_receptor_sequence(chain_res, cif_path, "CIF")


def _chain_sequence(residues: List[Tuple[int, str]]) -> str:
    """체인별 residue 목록을 1문자 서열로 변환한다."""
    return "".join(aa for _, aa in sorted(residues, key=lambda x: x[0]))


def _match_sstr_signature(receptor_sequence: str) -> Optional[Tuple[str, str, str]]:
    """SSTR signature 매칭 결과를 로깅 없이 반환한다."""
    seq_upper = receptor_sequence.upper()
    for sstr_name, signatures in _SSTR_SIGNATURES.items():
        for sig in signatures:
            if sig in seq_upper:
                return sstr_name, SSTR_UNIPROT[sstr_name], sig
    return None


def _select_receptor_sequence(
    chain_res: Dict[str, List[Tuple[int, str]]],
    source_path: str,
    fmt_name: str,
) -> str:
    """복합체 구조에서 실제 SSTR 수용체 체인을 선택한다.

    8XIR 같은 GPCR-G protein 복합체는 G-protein 체인이 SSTR 체인보다 길 수 있다.
    따라서 SSTR1~5 signature가 있는 체인을 먼저 고르고, 매칭 체인이 없을 때만
    기존 동작처럼 가장 긴 체인으로 폴백한다.
    """
    chain_seqs = {chain_id: _chain_sequence(residues) for chain_id, residues in chain_res.items()}

    matches: List[Tuple[str, str, str, str, str]] = []
    for chain_id, seq in chain_seqs.items():
        match = _match_sstr_signature(seq)
        if match:
            sstr_name, uniprot_id, signature = match
            matches.append((chain_id, seq, sstr_name, uniprot_id, signature))

    if matches:
        chain_id, seq, sstr_name, uniprot_id, signature = max(
            matches, key=lambda item: len(item[1])
        )
        logger.info(
            "%s SSTR 체인 선택: %s, %d aa, %s/%s (시그니처: %s, 파일: %s)",
            fmt_name, chain_id, len(seq), sstr_name, uniprot_id, signature, source_path,
        )
        return seq

    best_chain = max(chain_seqs, key=lambda c: len(chain_seqs[c]))
    seq = chain_seqs[best_chain]
    logger.info(
        "%s 서열 추출 완료: 체인 %s, %d aa (SSTR signature 미검출, 최장 체인 폴백)",
        fmt_name, best_chain, len(seq),
    )
    return seq


# ---------------------------------------------------------------------------
# SSTR UniProt ID 조회
# ---------------------------------------------------------------------------

def _find_sstr_uniprot(receptor_sequence: str) -> Optional[str]:
    """수용체 서열에서 SSTR UniProt accession을 조회한다.

    SSTR1~5의 특징 서열을 순서대로 비교하여 가장 먼저 매칭되는 것을 반환한다.

    Args:
        receptor_sequence: 수용체 아미노산 서열 (대소문자 무관)

    Returns:
        UniProt accession (예: "P30874") 또는 None
    """
    match = _match_sstr_signature(receptor_sequence)
    if match:
        sstr_name, upid, sig = match
        logger.info("SSTR 서열 매칭 성공: %s → UniProt %s (시그니처: %s)",
                    sstr_name, upid, sig)
        return upid
    logger.warning(
        "SSTR 서열 매칭 실패. 수용체 서열 앞 30aa: %s...", receptor_sequence[:30]
    )
    return None


# ---------------------------------------------------------------------------
# AlphaFoldDB MSA 다운로드 + 캐시
# ---------------------------------------------------------------------------

def _get_af_msa_url(uniprot_id: str) -> str:
    """AlphaFoldDB REST API로 MSA URL을 동적 조회한다.

    실패 시 v6 직접 URL 패턴으로 폴백한다.

    Args:
        uniprot_id: UniProt accession

    Returns:
        a3m 파일 URL
    """
    api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    try:
        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        if isinstance(data, list) and data:
            msa_url = data[0].get("msaUrl", "")
            if msa_url:
                logger.info("AlphaFoldDB API MSA URL 조회 성공: %s", msa_url)
                return msa_url
    except Exception as exc:
        logger.warning("AlphaFoldDB API 조회 실패 (%s): %s — 직접 URL 사용", uniprot_id, exc)

    # 폴백: v6 직접 URL 패턴
    fallback = f"https://alphafold.ebi.ac.uk/files/msa/AF-{uniprot_id}-F1-msa_v6.a3m"
    logger.info("MSA URL 폴백 사용: %s", fallback)
    return fallback


def _download_af_msa(
    uniprot_id: str,
    cache_dir: Path = _DEFAULT_MSA_CACHE,
) -> Path:
    """AlphaFoldDB MSA를 다운로드하고 캐시에 저장한다.

    캐시에 유효한 파일이 있으면 다운로드를 건너뛴다.

    Args:
        uniprot_id: UniProt accession
        cache_dir:  로컬 캐시 디렉토리 (기본: ~/.cache/boltz_msa/)

    Returns:
        로컬 a3m 파일 경로

    Raises:
        RuntimeError: 다운로드 실패 (네트워크 오류 또는 파일 없음)
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{uniprot_id}.a3m"

    if cached.exists() and cached.stat().st_size > 100:
        logger.info("AlphaFoldDB MSA 캐시 사용: %s (%.1f MB)",
                    cached, cached.stat().st_size / 1e6)
        return cached

    msa_url = _get_af_msa_url(uniprot_id)
    logger.info("AlphaFoldDB MSA 다운로드 시작: %s", msa_url)

    tmp_path = cached.with_suffix(".a3m.tmp")
    try:
        urllib.request.urlretrieve(msa_url, tmp_path)
        tmp_path.rename(cached)
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        raise RuntimeError(
            f"AlphaFoldDB MSA 다운로드 실패 (UniProt: {uniprot_id})\n"
            f"  URL: {msa_url}\n"
            f"  오류: {exc}\n"
            f"\n"
            f"수동 다운로드 후 다음 경로에 저장하세요:\n"
            f"  {cached}\n"
            f"\n"
            f"다운로드 명령:\n"
            f"  curl -sL '{msa_url}' -o '{cached}'\n"
            f"\n"
            f"KAERI 내부망 환경 우회 상세: docs/boltz2_offline_workaround.md"
        ) from exc

    logger.info("MSA 다운로드 완료: %s (%.1f MB)", cached, cached.stat().st_size / 1e6)
    return cached


# ---------------------------------------------------------------------------
# Boltz YAML 입력 파일 생성
# ---------------------------------------------------------------------------

def _write_boltz_yaml(
    peptide_seq: str,
    receptor_seq: str,
    pep_msa_path: Path,
    rec_msa_path: Path,
    yaml_path: Path,
) -> None:
    """Boltz-2 입력 YAML을 생성한다.

    펩타이드(chain A)와 수용체(chain B)를 각각 MSA 경로와 함께 지정한다.
    MSA 경로는 반드시 절대 경로여야 한다 (Boltz 요구사항).

    Args:
        peptide_seq:  펩타이드 아미노산 서열
        receptor_seq: 수용체 아미노산 서열
        pep_msa_path: 펩타이드 self-only a3m (절대 경로)
        rec_msa_path: 수용체 AlphaFoldDB a3m (절대 경로)
        yaml_path:    출력 YAML 파일 경로
    """
    content = (
        "version: 1\n"
        "sequences:\n"
        "  - protein:\n"
        f"      id: A\n"
        f"      sequence: {peptide_seq}\n"
        f"      msa: {pep_msa_path.resolve()}\n"
        "  - protein:\n"
        f"      id: B\n"
        f"      sequence: {receptor_seq}\n"
        f"      msa: {rec_msa_path.resolve()}\n"
    )
    yaml_path.write_text(content)
    logger.debug("Boltz YAML 생성: %s", yaml_path)


# ---------------------------------------------------------------------------
# Boltz subprocess 실행
# ---------------------------------------------------------------------------

def _run_boltz_subprocess(
    yaml_path: Path,
    out_dir: Path,
    diffusion_samples: int,
    cuda_device: str,
    recycling_steps: int = 1,
    sampling_steps: int = 50,
) -> None:
    """Boltz-2를 subprocess로 실행한다.

    KAERI 내부망 필수 옵션:
        --no_kernels    : libnvrtc.so.12 누락 우회 (CUDA NVRTC 비활성)
        --num_workers 0 : multiprocessing DataLoader 충돌 방지

    Args:
        yaml_path:         Boltz 입력 YAML 경로
        out_dir:           Boltz 출력 루트 디렉토리
        diffusion_samples: 생성 구조 수 (nstruct에 대응)
        cuda_device:       사용 GPU 번호 문자열 (예: "0", "2")
        recycling_steps:   Boltz recycling 스텝 수
        sampling_steps:    Boltz diffusion sampling 스텝 수

    Raises:
        RuntimeError: subprocess 실패
    """
    boltz_env = os.environ.get("OFFTARGET_DOCK_BOLTZ_ENV", "boltz")
    cmd = [
        "conda", "run", "--no-capture-output", "-n", boltz_env,
        "boltz", "predict", str(yaml_path),
        "--out_dir", str(out_dir),
        "--recycling_steps", str(recycling_steps),
        "--sampling_steps", str(sampling_steps),
        "--diffusion_samples", str(diffusion_samples),
        "--output_format", "pdb",
        "--override",
        "--num_workers", "0",
        "--no_kernels",
    ]

    env = {**os.environ, "CUDA_VISIBLE_DEVICES": cuda_device}
    logger.info(
        "Boltz 실행: env=%s, CUDA_VISIBLE_DEVICES=%s, diffusion_samples=%d",
        boltz_env, cuda_device, diffusion_samples,
    )
    logger.debug("명령: %s", " ".join(cmd))

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )

    if proc.returncode != 0:
        stderr_tail = proc.stderr[-600:] if proc.stderr else "(stderr 없음)"
        raise RuntimeError(
            f"Boltz subprocess 실패 (returncode={proc.returncode}):\n"
            f"{stderr_tail}"
        )


# ---------------------------------------------------------------------------
# Boltz 결과 파싱
# ---------------------------------------------------------------------------

def _parse_best_confidence(
    boltz_out_dir: Path,
    yaml_stem: str,
) -> Tuple[Dict[str, Any], Optional[Path]]:
    """Boltz 출력에서 최고 iPTM 모델의 confidence JSON과 PDB 경로를 반환한다.

    Args:
        boltz_out_dir: Boltz 출력 루트 (`--out_dir`)
        yaml_stem:     YAML 파일명 (확장자 제외)

    Returns:
        (confidence_dict, best_pdb_path)

    Raises:
        RuntimeError: confidence 파일을 찾을 수 없는 경우
    """
    result_dir = boltz_out_dir / f"boltz_results_{yaml_stem}"
    conf_files = sorted(result_dir.rglob("confidence_*_model_*.json"))

    if not conf_files:
        # 디렉토리 상태 디버깅
        found = list(boltz_out_dir.rglob("*.json"))[:10]
        raise RuntimeError(
            f"Boltz confidence 파일 없음.\n"
            f"  탐색 디렉토리: {result_dir}\n"
            f"  발견된 JSON 파일: {found}"
        )

    best_conf: Dict[str, Any] = {}
    best_iptm: float = -1.0
    best_pdb: Optional[Path] = None

    for conf_file in conf_files:
        try:
            conf = json.loads(conf_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        iptm = float(conf.get("iptm", -1.0))
        if iptm > best_iptm:
            best_iptm = iptm
            best_conf = conf
            # 대응 PDB: confidence_<stem>_model_N.json → <stem>_model_N.pdb
            pdb_stem = conf_file.stem.replace("confidence_", "")
            pdb_candidates = list(conf_file.parent.glob(f"{pdb_stem}.pdb"))
            if not pdb_candidates:
                pdb_candidates = sorted(conf_file.parent.glob("*.pdb"))
            best_pdb = pdb_candidates[0] if pdb_candidates else None

    if not best_conf:
        raise RuntimeError(f"유효한 confidence 결과 없음 (탐색: {conf_files})")

    logger.info(
        "Boltz 결과 파싱 완료: iPTM=%.3f, pTM=%.3f, confidence=%.3f",
        best_conf.get("iptm", 0),
        best_conf.get("ptm", 0),
        best_conf.get("confidence_score", 0),
    )
    return best_conf, best_pdb


# ---------------------------------------------------------------------------
# ddG 프록시 계산
# ---------------------------------------------------------------------------

def _compute_ddg_proxy(iptm: float, method: str = "linear") -> float:
    """iPTM 값에서 ddG 프록시를 계산한다.

    두 가지 방법을 지원한다:
      - linear: ddg = -100 * iptm
        단순 선형 스케일링. 하위 호환성 보장.
      - boltz:  ddg = -RT * ln(iptm / (1 - iptm))
        열역학적으로 의미 있는 자유에너지 프록시 (Boltz 논문 권고).
        RT = 0.616 kcal/mol (310 K 체온 기준)

    selectivity_runner.py 가 "ddg" 키를 float으로 읽으므로
    음수(강결합) / 0(약결합) 방향이 유지되어야 한다.

    Args:
        iptm:   iPTM 값 (0 ~ 1)
        method: "linear" (기본) 또는 "boltz"

    Returns:
        ddG 프록시 (kcal/mol 단위, 음수 = 강결합)
    """
    if method == "boltz":
        import math
        eps = 1e-6
        clamped = max(eps, min(1.0 - eps, iptm))
        rt = 0.616  # kcal/mol at 310 K
        return -rt * math.log(clamped / (1.0 - clamped))
    # linear (기본)
    return -100.0 * iptm


# ---------------------------------------------------------------------------
# 메인 도킹 함수
# ---------------------------------------------------------------------------

def run_docking(
    receptor_path: str,
    sequence: str,
    nstruct: int = 1,
    output_dir: Optional[str] = None,
    msa_cache_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Boltz-2 + AlphaFoldDB MSA 도킹을 실행하고 결과를 반환한다.

    워크플로우:
        1. 수용체 PDB/CIF에서 아미노산 서열 추출
        2. 서열 → SSTR UniProt ID 매핑
        3. AlphaFoldDB MSA 다운로드 (캐시 우선, ~/.cache/boltz_msa/)
        4. 펩타이드 self-only a3m 생성
        5. Boltz-2 입력 YAML 작성
        6. Boltz-2 subprocess 실행 (--no_kernels --num_workers 0)
        7. confidence JSON 파싱 → iPTM 기반 ddG 프록시 계산

    Args:
        receptor_path:  수용체 CIF/PDB 파일 경로
        sequence:       펩타이드 아미노산 서열 (1문자 코드)
        nstruct:        생성 구조 수 (Boltz --diffusion_samples 에 대응)
                        Boltz는 nstruct=1로도 충분한 결과를 제공함.
                        PyRosetta의 nstruct=20 기본값은 Boltz에서 불필요.
        output_dir:     결과 저장 디렉토리. None이면 임시 디렉토리 사용.
        msa_cache_dir:  MSA 캐시 디렉토리. None이면 ~/.cache/boltz_msa/ 사용.

    Returns:
        {
            "ddg":        float,   # -100 * iptm (SelectivityRunner 하위 호환 키)
            "iptm":       float,   # interface predicted TM-score (0~1)
            "ptm":        float,   # predicted TM-score (0~1)
            "confidence": float,   # Boltz confidence_score (0~1)
            "best_pdb":   str|None,# 최적 구조 PDB 파일 경로
            "engine":     str      # "boltz-2"
        }

    Raises:
        RuntimeError: MSA 다운로드 실패 / Boltz subprocess 실패 / 결과 파싱 실패
    """
    cuda_device = os.environ.get("OFFTARGET_DOCK_CUDA_DEVICE", "0")
    cache_dir = msa_cache_dir or _DEFAULT_MSA_CACHE

    # ------------------------------------------------------------------
    # 1. 수용체 서열 추출
    # ------------------------------------------------------------------
    receptor_seq = _extract_sequence_from_pdb(receptor_path)

    # ------------------------------------------------------------------
    # 2. SSTR UniProt ID 조회
    # ------------------------------------------------------------------
    uniprot_id = _find_sstr_uniprot(receptor_seq)
    if uniprot_id is None:
        raise RuntimeError(
            "수용체 서열이 SSTR1/2/3/4/5 어느 것과도 매칭되지 않습니다.\n"
            "해결 방법:\n"
            "  1. AlphaFoldDB MSA를 수동 다운로드 후 cache_dir에 저장:\n"
            f"     {cache_dir}/<UniProt_ID>.a3m\n"
            "  2. offtarget_dock.py 의 SSTR_UNIPROT / _SSTR_SIGNATURES 맵에\n"
            "     새 수용체 정보를 추가하세요."
        )

    # ------------------------------------------------------------------
    # 3. AlphaFoldDB MSA 다운로드 (캐시 우선)
    # ------------------------------------------------------------------
    rec_msa_path = _download_af_msa(uniprot_id, cache_dir)

    # ------------------------------------------------------------------
    # 4. 작업 디렉토리 준비
    # ------------------------------------------------------------------
    _tmp_dir: Optional[str] = None
    if output_dir:
        work_dir = Path(output_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        _tmp_dir = tempfile.mkdtemp(prefix="offtarget_dock_")
        work_dir = Path(_tmp_dir)

    try:
        # YAML 식별자: 펩타이드 앞 8자 + 수용체 UniProt
        yaml_stem = f"dock_{sequence[:8]}_{uniprot_id}"
        yaml_path = work_dir / f"{yaml_stem}.yaml"
        pep_msa_path = work_dir / f"{yaml_stem}_peptide.a3m"

        # ------------------------------------------------------------------
        # 5. 펩타이드 self-only a3m 생성
        # ------------------------------------------------------------------
        pep_msa_path.write_text(f">query\n{sequence}\n")
        logger.info("펩타이드 self-only a3m 생성: %s", pep_msa_path)

        # ------------------------------------------------------------------
        # 6. Boltz YAML 생성
        # ------------------------------------------------------------------
        _write_boltz_yaml(
            peptide_seq=sequence,
            receptor_seq=receptor_seq,
            pep_msa_path=pep_msa_path,
            rec_msa_path=rec_msa_path,
            yaml_path=yaml_path,
        )

        # ------------------------------------------------------------------
        # 7. Boltz subprocess 실행
        # ------------------------------------------------------------------
        boltz_out = work_dir / "boltz_out"
        boltz_out.mkdir(exist_ok=True)
        _run_boltz_subprocess(
            yaml_path=yaml_path,
            out_dir=boltz_out,
            diffusion_samples=max(1, nstruct),
            cuda_device=cuda_device,
        )

        # ------------------------------------------------------------------
        # 8. 결과 파싱
        # ------------------------------------------------------------------
        conf, best_pdb_src = _parse_best_confidence(boltz_out, yaml_stem)

        iptm = float(conf.get("iptm", 0.0))
        ptm = float(conf.get("ptm", 0.0))
        confidence = float(conf.get("confidence_score", 0.0))

        # ------------------------------------------------------------------
        # 9. 최적 PDB 복사 (output_dir 지정 시)
        # ------------------------------------------------------------------
        best_pdb: Optional[str] = None
        if best_pdb_src and best_pdb_src.exists():
            if output_dir:
                dest = Path(output_dir) / "best_dock.pdb"
                shutil.copy2(str(best_pdb_src), str(dest))
                best_pdb = str(dest)
            else:
                best_pdb = str(best_pdb_src)

        # ------------------------------------------------------------------
        # 10. ddG 프록시 계산 (-100 * iptm, 하위 호환)
        # ------------------------------------------------------------------
        ddg = _compute_ddg_proxy(iptm, method="linear")

        return {
            "ddg": round(ddg, 3),
            "iptm": round(iptm, 4),
            "ptm": round(ptm, 4),
            "confidence": round(confidence, 4),
            "best_pdb": best_pdb,
            "engine": "boltz-2",
        }

    finally:
        # 임시 디렉토리 정리 (output_dir 없는 경우)
        if _tmp_dir and not output_dir:
            shutil.rmtree(_tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI 엔트리포인트
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(
        description=(
            "Boltz-2 + AlphaFoldDB MSA off-target docking "
            "(PyRosetta FlexPepDock 대체)"
        )
    )
    parser.add_argument(
        "--receptor",
        required=True,
        help="수용체 구조 파일 경로 (CIF/PDB)",
    )
    parser.add_argument(
        "--sequence",
        required=True,
        help="펩타이드 아미노산 서열 (1문자 코드)",
    )
    parser.add_argument(
        "--nstruct",
        type=int,
        default=1,
        help=(
            "생성 구조 수 (Boltz --diffusion_samples에 매핑, 기본 1). "
            "Boltz는 nstruct=1로도 신뢰할 수 있는 결과를 제공함."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="결과 저장 디렉토리 (None이면 임시 디렉토리 사용 후 삭제)",
    )
    args = parser.parse_args()

    try:
        result = run_docking(
            receptor_path=args.receptor,
            sequence=args.sequence,
            nstruct=args.nstruct,
            output_dir=args.output_dir,
        )
        print(json.dumps(result), flush=True)
    except Exception as exc:
        logger.exception("offtarget_dock 실패")
        print(json.dumps({"error": str(exc)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
