#!/usr/bin/env python
"""
run_proteinmpnn.py
==================
ProteinMPNN / LigandMPNN 로컬 실행 래퍼.

step03_sequence.py의 design_for_backbone()이 기대하는 출력 형식을 반환한다.
binder 체인(chain A)에 대한 역폴딩(inverse folding) 서열을 설계한다.

Output JSON:
    {"sequences": [{"sequence": "AGCK...", "score": -1.5}, ...]}
    또는 에러 시:
    {"error": "<message>"}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ProteinMPNN 로컬 실행 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--input-json",
        default=None,
        help="JSON payload 파일 경로 (다른 인자를 override)",
    )
    parser.add_argument("--backbone-pdb", default=None, help="백본 PDB 파일 경로")
    parser.add_argument("--num-seqs", type=int, default=8, help="생성할 서열 수")
    parser.add_argument(
        "--temperature", type=float, default=0.1, help="샘플링 온도 (낮을수록 보수적)"
    )
    parser.add_argument("--output-dir", required=True, help="출력 파일 저장 디렉토리")
    args = parser.parse_args()

    if args.input_json:
        import tempfile

        with open(args.input_json) as f:
            payload = json.load(f)

        backbone_pdb_text = payload.get("backbone_pdb", "")
        if backbone_pdb_text:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".pdb", delete=False,
                dir=args.output_dir if args.output_dir else None,
            )
            tmp.write(backbone_pdb_text)
            tmp.flush()
            tmp.close()
            args.backbone_pdb = tmp.name
        elif args.backbone_pdb is None:
            parser.error("--input-json의 backbone_pdb 키가 없고 --backbone-pdb도 지정되지 않음")

        args.num_seqs = int(payload.get("num_seqs", args.num_seqs))
        args.temperature = float(payload.get("temperature", args.temperature))
    else:
        if args.backbone_pdb is None:
            parser.error("--backbone-pdb 또는 --input-json 중 하나를 지정해야 합니다.")

    return args


def _run_ligandmpnn(
    backbone_pdb: str,
    num_seqs: int,
    temperature: float,
    output_dir: Path,
) -> List[Dict[str, Any]]:
    """LigandMPNN Python API를 사용하여 서열을 설계한다.

    LigandMPNN은 ProteinMPNN의 확장판으로 리간드 컨텍스트를 지원한다.
    체인 A(binder)에 대해서만 서열 설계를 수행한다.
    """
    import torch

    # LigandMPNN 모듈 경로 탐색
    # conda 환경에 설치되어 있거나 site-packages에 있어야 함
    try:
        from ligandmpnn.run import run as ligandmpnn_run  # type: ignore
    except ImportError:
        raise ImportError(
            "LigandMPNN이 설치되지 않음. "
            "conda 환경에 LigandMPNN이 설치되어 있어야 합니다."
        )

    # LigandMPNN CLI 인터페이스가 없으면 subprocess로 폴백
    raise ImportError("API 방식 불가 — subprocess 폴백 사용")


def _run_ligandmpnn_cli(
    backbone_pdb: str,
    num_seqs: int,
    temperature: float,
    output_dir: Path,
) -> List[Dict[str, Any]]:
    """ligandmpnn CLI를 subprocess로 호출하여 서열 설계."""
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "ligandmpnn",
            "--model_type", "protein_mpnn",
            "--pdb_path", backbone_pdb,
            "--out_folder", tmpdir,
            "--number_of_batches", str(num_seqs),
            "--temperature", str(temperature),
            "--batch_size", "1",
        ]
        print(f"[LigandMPNN CLI] {' '.join(cmd[:6])}...", file=sys.stderr)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(f"ligandmpnn CLI 실패 (exit {proc.returncode}): {proc.stderr[:200]}")

        # 결과 FASTA 파싱
        sequences: List[Dict[str, Any]] = []
        seqs_dir = Path(tmpdir) / "seqs"
        if seqs_dir.exists():
            for fasta in sorted(seqs_dir.glob("*.fa")):
                for line in fasta.read_text().splitlines():
                    if line.startswith(">"):
                        # 헤더에서 score 추출: >T=0.1, sample=1, score=1.234
                        score = 0.0
                        for part in line.split(","):
                            if "score" in part:
                                try:
                                    score = float(part.split("=")[-1].strip())
                                except ValueError:
                                    pass
                    elif line.strip():
                        sequences.append({"sequence": line.strip(), "score": score})

        if not sequences:
            raise RuntimeError("ligandmpnn CLI가 서열을 생성하지 못함")
        return sequences


def _run_proteinmpnn_subprocess(
    backbone_pdb: str,
    num_seqs: int,
    temperature: float,
    output_dir: Path,
) -> List[Dict[str, Any]]:
    """ProteinMPNN을 subprocess로 실행하고 결과를 파싱한다.

    ProteinMPNN의 표준 protein_mpnn_run.py 또는 LigandMPNN을 호출한다.
    """
    import subprocess
    import tempfile
    import re

    # ProteinMPNN 설치 경로 탐색
    # 1순위: conda 환경 내 protein_mpnn 패키지
    # 2순위: esm 기반 역폴딩 폴백
    mpnn_script = None
    search_paths = [
        Path(sys.prefix) / "lib" / "python3.10" / "site-packages" / "protein_mpnn" / "protein_mpnn_run.py",
        Path(sys.prefix) / "lib" / "python3.9" / "site-packages" / "protein_mpnn" / "protein_mpnn_run.py",
        Path("/opt/conda/envs/proteinmpnn/protein_mpnn_run.py"),
        Path.home() / "ProteinMPNN" / "protein_mpnn_run.py",
    ]
    for path in search_paths:
        if path.exists():
            mpnn_script = path
            break

    if mpnn_script is None:
        # protein_mpnn_run.py 없으면 ligandmpnn CLI로 폴백
        import shutil
        ligandmpnn_bin = shutil.which("ligandmpnn")
        if ligandmpnn_bin:
            return _run_ligandmpnn_cli(backbone_pdb, num_seqs, temperature, output_dir)
        raise FileNotFoundError(
            "ProteinMPNN/LigandMPNN을 찾을 수 없음. "
            "ligandmpnn 또는 protein_mpnn_run.py를 설치하세요."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # ProteinMPNN CLI 실행
        cmd = [
            sys.executable,
            str(mpnn_script),
            "--pdb_path", backbone_pdb,
            "--pdb_path_chains", "A",     # binder 체인만 설계
            "--out_folder", str(tmp_path),
            "--num_seq_per_target", str(num_seqs),
            "--sampling_temp", str(temperature),
            "--seed", "42",
            "--batch_size", "1",
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ProteinMPNN 실행 실패 (exit {result.returncode})"
            )

        # 출력 FASTA 파일 파싱
        fasta_files = sorted(tmp_path.glob("**/*.fa")) + sorted(tmp_path.glob("**/*.fasta"))
        sequences: List[Dict[str, Any]] = []
        for fasta_file in fasta_files:
            lines = fasta_file.read_text(encoding="utf-8").splitlines()
            current_header = ""
            current_seq = []
            for line in lines:
                if line.startswith(">"):
                    if current_seq and current_header:
                        # score는 헤더에서 추출 (예: score=1.234)
                        score_match = re.search(r"score=([0-9.\-]+)", current_header)
                        score = float(score_match.group(1)) if score_match else 0.0
                        # 첫 번째 서열은 original이므로 건너뜀
                        if "T=0" in current_header or "sample" in current_header:
                            sequences.append(
                                {"sequence": "".join(current_seq).upper(), "score": score}
                            )
                    current_header = line
                    current_seq = []
                else:
                    current_seq.append(line.strip())
            if current_seq and current_header:
                score_match = re.search(r"score=([0-9.\-]+)", current_header)
                score = float(score_match.group(1)) if score_match else 0.0
                if "T=0" in current_header or "sample" in current_header:
                    sequences.append(
                        {"sequence": "".join(current_seq).upper(), "score": score}
                    )

        return sequences[:num_seqs]


def _run_esm_if_fallback(
    backbone_pdb: str,
    num_seqs: int,
    temperature: float,
) -> List[Dict[str, Any]]:
    """ESM-IF (inverse folding) 폴백.

    ProteinMPNN 설치가 없을 때 ESM-IF로 역폴딩을 수행한다.
    """
    import torch

    try:
        import esm
        import esm.inverse_folding  # type: ignore
    except ImportError:
        raise ImportError(
            "ESM 패키지가 없어 역폴딩 폴백 불가. "
            "pip install fair-esm 또는 ProteinMPNN을 설치하세요."
        )

    model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()

    # PDB에서 구조 로드
    structure = esm.inverse_folding.util.load_structure(backbone_pdb, chain_id="A")
    coords, native_seq = esm.inverse_folding.util.extract_coords_from_structure(structure)

    sequences: List[Dict[str, Any]] = []
    for _ in range(num_seqs):
        with torch.no_grad():
            sampled_seq = model.sample(
                coords,
                temperature=temperature,
                device=next(model.parameters()).device,
            )
        sequences.append({"sequence": sampled_seq.upper(), "score": 0.0})

    return sequences


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sequences: List[Dict[str, Any]] = []

    # 실행 순서: ProteinMPNN subprocess → ESM-IF 폴백
    try:
        sequences = _run_proteinmpnn_subprocess(
            backbone_pdb=str(Path(args.backbone_pdb).resolve()),
            num_seqs=args.num_seqs,
            temperature=args.temperature,
            output_dir=out_dir,
        )
        print(f"[ProteinMPNN] {len(sequences)}개 서열 생성 완료", file=sys.stderr)
    except (FileNotFoundError, RuntimeError) as exc:
        print(
            f"[ProteinMPNN] subprocess 실패: {exc}. ESM-IF 폴백 시도...",
            file=sys.stderr,
        )
        try:
            sequences = _run_esm_if_fallback(
                backbone_pdb=str(Path(args.backbone_pdb).resolve()),
                num_seqs=args.num_seqs,
                temperature=args.temperature,
            )
            print(
                f"[ESM-IF] {len(sequences)}개 서열 생성 완료", file=sys.stderr
            )
        except Exception as exc2:
            print(
                json.dumps({"error": f"ProteinMPNN 및 ESM-IF 모두 실패: {exc2}"}),
                flush=True,
            )
            sys.exit(1)

    if not sequences:
        print(
            json.dumps({"error": "서열 생성 결과 없음"}), flush=True
        )
        sys.exit(1)

    # FASTA 파일로도 저장
    fasta_path = out_dir / "sequences.fasta"
    fasta_lines = []
    for idx, entry in enumerate(sequences):
        fasta_lines.append(f">design_{idx:04d} score={entry.get('score', 0.0):.4f}")
        fasta_lines.append(entry["sequence"])
    fasta_path.write_text("\n".join(fasta_lines) + "\n", encoding="utf-8")
    print(f"[ProteinMPNN] FASTA 저장: {fasta_path}", file=sys.stderr)

    print(json.dumps({"sequences": sequences}), flush=True)


if __name__ == "__main__":
    main()
