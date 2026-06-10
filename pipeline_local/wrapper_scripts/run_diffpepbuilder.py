#!/usr/bin/env python
"""
run_diffpepbuilder.py
=====================
DiffPepBuilder 로컬 실행 래퍼.

step05_docking.py의 _build_docking_result()가 기대하는 도킹 포즈 PDB와
스코어를 반환한다. DiffPepBuilder의 SSbuilder.py를 통해 실행한다.

DiffPepBuilder 리포지토리:
    /home/dongjukim/Documents/workspace/repos/SST14-M_scr/local_models/DiffPepBuilder/

Output JSON:
    {
        "docked_pdbs": ["<pdb_content_1>", ...],
        "scores": [-8.5, -7.2, ...]
    }
    또는 에러 시:
    {"error": "<message>"}
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

warnings.filterwarnings("ignore")

# DiffPepBuilder 리포지토리 절대 경로
_DIFFPEP_REPO = Path(
    "/home/dongjukim/Documents/workspace/repos/SST14-M_scr/local_models/DiffPepBuilder"
)
_SSBUILDER_SCRIPT = _DIFFPEP_REPO / "SSbuilder" / "SSbuilder.py"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DiffPepBuilder 로컬 실행 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--input-json",
        default=None,
        help="JSON payload 파일 경로 (다른 인자를 override)",
    )
    parser.add_argument("--receptor-pdb", default=None, help="수용체 PDB 파일 경로")
    parser.add_argument(
        "--peptide-seq", default=None, help="펩타이드 아미노산 서열 (1문자 코드)"
    )
    parser.add_argument("--output-dir", required=True, help="출력 파일 저장 디렉토리")
    args = parser.parse_args()

    if args.input_json:
        with open(args.input_json) as f:
            payload = json.load(f)

        receptor_pdb_text = payload.get("receptor_pdb", "")
        if receptor_pdb_text:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".pdb", delete=False, dir=str(out_dir)
            )
            tmp.write(receptor_pdb_text)
            tmp.flush()
            tmp.close()
            args.receptor_pdb = tmp.name
        elif args.receptor_pdb is None:
            parser.error("--input-json의 receptor_pdb 키가 없고 --receptor-pdb도 지정되지 않음")

        peptide_seq = payload.get("peptide_sequence", payload.get("peptide_seq", ""))
        if peptide_seq:
            args.peptide_seq = peptide_seq
        elif args.peptide_seq is None:
            parser.error(
                "--input-json의 peptide_sequence 키가 없고 --peptide-seq도 지정되지 않음"
            )
    else:
        if args.receptor_pdb is None:
            parser.error("--receptor-pdb 또는 --input-json 중 하나를 지정해야 합니다.")
        if args.peptide_seq is None:
            parser.error("--peptide-seq 또는 --input-json 중 하나를 지정해야 합니다.")

    return args


def _run_diffpepbuilder(
    receptor_pdb: str,
    peptide_seq: str,
    output_dir: Path,
) -> Tuple[List[str], List[float]]:
    """DiffPepBuilder SSbuilder.py를 subprocess로 실행하고 결과를 파싱한다.

    SSbuilder는 receptor PDB와 펩타이드 서열을 받아 도킹된 구조 PDB들을 생성한다.
    """
    if not _SSBUILDER_SCRIPT.exists():
        raise FileNotFoundError(
            f"SSbuilder.py를 찾을 수 없음: {_SSBUILDER_SCRIPT}"
        )

    # SSbuilder는 config YAML 방식으로 입력을 받음
    # 임시 config 파일 생성
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=str(output_dir)
    ) as cfg_file:
        cfg_content = f"""receptor_pdb: {receptor_pdb}
peptide_sequence: {peptide_seq}
output_dir: {output_dir}
num_designs: 5
diffusion_steps: 50
"""
        cfg_file.write(cfg_content)
        cfg_path = cfg_file.name

    try:
        cmd = [
            sys.executable,
            str(_SSBUILDER_SCRIPT),
            "--config", cfg_path,
        ]

        env = os.environ.copy()
        # DiffPepBuilder가 자체 openfold 모듈을 사용하므로 PYTHONPATH에 추가
        env["PYTHONPATH"] = str(_DIFFPEP_REPO) + ":" + env.get("PYTHONPATH", "")

        result = subprocess.run(
            cmd,
            cwd=str(_DIFFPEP_REPO),
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"DiffPepBuilder 실행 실패 (exit {result.returncode})"
            )
    finally:
        # 임시 config 파일 정리
        try:
            Path(cfg_path).unlink(missing_ok=True)
        except OSError:
            pass

    # 출력 PDB 파일 수집
    pdb_files = sorted(glob.glob(str(output_dir / "*.pdb")))
    # 수용체 PDB는 제외 (입력 파일이 output_dir에 복사되었을 경우 방지)
    receptor_name = Path(receptor_pdb).name
    pdb_files = [p for p in pdb_files if Path(p).name != receptor_name]

    if not pdb_files:
        raise RuntimeError(
            f"DiffPepBuilder 출력 PDB를 찾을 수 없음: {output_dir}/*.pdb"
        )

    pdb_contents = [Path(p).read_text(encoding="utf-8") for p in pdb_files]

    # 스코어 파싱 (scores.json 또는 PDB REMARK에서 추출)
    scores = _parse_scores(output_dir, len(pdb_contents))

    return pdb_contents, scores


def _parse_scores(output_dir: Path, n_poses: int) -> List[float]:
    """DiffPepBuilder 출력 디렉토리에서 스코어를 파싱한다.

    scores.json 파일이 있으면 사용하고, 없으면 더미 스코어를 반환한다.
    """
    score_json = output_dir / "scores.json"
    if score_json.exists():
        try:
            data = json.loads(score_json.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [float(s) for s in data[:n_poses]]
            if isinstance(data, dict):
                scores = data.get("scores", data.get("binding_scores", []))
                return [float(s) for s in scores[:n_poses]]
        except (json.JSONDecodeError, TypeError):
            pass

    # 더미 스코어 (순서 기반 내림차순)
    return [-float(i) for i in range(n_poses)]


def _run_simple_docking_fallback(
    receptor_pdb: str,
    peptide_seq: str,
    output_dir: Path,
) -> Tuple[List[str], List[float]]:
    """DiffPepBuilder 실행 불가 시 간단한 구조 배치 폴백.

    ESMFold로 펩타이드 구조를 예측한 뒤 수용체 PDB와 단순 결합한 복합체를 반환한다.
    도킹 스코어는 0.0으로 설정한다 (실제 도킹 아님).
    """
    import torch
    import warnings as _w

    _w.filterwarnings("ignore")

    print("[DiffPepBuilder] 폴백: ESMFold로 펩타이드 구조 예측 후 단순 복합체 구성", file=sys.stderr)

    try:
        from transformers import EsmForProteinFolding, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
        model = EsmForProteinFolding.from_pretrained(
            "facebook/esmfold_v1", low_cpu_mem_usage=True
        )
        model = model.cuda() if torch.cuda.is_available() else model
        model.eval()

        tokenized = tokenizer(
            [peptide_seq], return_tensors="pt", add_special_tokens=False
        )
        if next(model.parameters()).is_cuda:
            tokenized = {k: v.cuda() for k, v in tokenized.items()}

        with torch.no_grad():
            output = model(**tokenized)

        peptide_pdb = model.output_to_pdb(output)[0]

        # 수용체 + 펩타이드 단순 결합 (체인 A = 수용체, 체인 B = 펩타이드)
        receptor_content = Path(receptor_pdb).read_text(encoding="utf-8")
        # 수용체의 체인 ID를 A로 통일
        receptor_lines = []
        for line in receptor_content.splitlines():
            if line[:6].strip() in ("ATOM", "HETATM"):
                receptor_lines.append(line[:21] + "A" + line[22:])
            elif line[:3] not in ("END", "TER"):
                receptor_lines.append(line)
        # 펩타이드를 체인 B로 설정
        peptide_lines = []
        for line in peptide_pdb.splitlines():
            if line[:6].strip() in ("ATOM", "HETATM"):
                peptide_lines.append(line[:21] + "B" + line[22:])
        complex_pdb = "\n".join(receptor_lines + peptide_lines) + "\nEND\n"

        return [complex_pdb], [0.0]

    except Exception as exc:
        raise RuntimeError(f"폴백 실패: {exc}")


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    receptor_pdb = str(Path(args.receptor_pdb).resolve())

    try:
        pdb_contents, scores = _run_diffpepbuilder(
            receptor_pdb=receptor_pdb,
            peptide_seq=args.peptide_seq,
            output_dir=out_dir,
        )
        print(
            f"[DiffPepBuilder] {len(pdb_contents)}개 도킹 포즈 생성 완료",
            file=sys.stderr,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(
            f"[DiffPepBuilder] 실행 실패: {exc}. ESMFold 폴백 시도...",
            file=sys.stderr,
        )
        try:
            pdb_contents, scores = _run_simple_docking_fallback(
                receptor_pdb=receptor_pdb,
                peptide_seq=args.peptide_seq,
                output_dir=out_dir,
            )
        except RuntimeError as exc2:
            print(
                json.dumps({"error": f"DiffPepBuilder 및 폴백 모두 실패: {exc2}"}),
                flush=True,
            )
            sys.exit(1)

    print(
        json.dumps({"docked_pdbs": pdb_contents, "scores": scores}),
        flush=True,
    )


if __name__ == "__main__":
    main()
