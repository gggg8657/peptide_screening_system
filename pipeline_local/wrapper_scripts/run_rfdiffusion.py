#!/usr/bin/env python
"""
run_rfdiffusion.py
==================
RFdiffusion 로컬 실행 래퍼.

conda run 환경에서 실행되며, hydra 기반 run_inference.py를 subprocess로 호출한다.
stdout에는 JSON 결과만 출력한다.

Output JSON:
    {"output_pdbs": ["<pdb_text_1>", ...]}
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
from pathlib import Path
from typing import List, Optional, Union

# RFdiffusion 리포지토리 절대 경로
_RFDIFFUSION_REPO = Path(
    "/home/dongjukim/Documents/workspace/repos/SST14-M_scr/local_models/RFdiffusion"
)
_INFERENCE_SCRIPT = _RFDIFFUSION_REPO / "scripts" / "run_inference.py"

# --input-json 모드에서 receptor PDB 텍스트를 저장할 임시 파일 핸들
_tmp_receptor_file: Optional[tempfile.NamedTemporaryFile] = None  # type: ignore[assignment]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RFdiffusion 로컬 실행 래퍼 — stdout에 JSON 출력"
    )
    parser.add_argument(
        "--input-json",
        default=None,
        help="JSON payload 파일 경로 (다른 인자를 override)",
    )
    parser.add_argument("--receptor-pdb", default=None, help="수용체 PDB 파일 경로")
    parser.add_argument(
        "--contigs",
        default=None,
        help="RFdiffusion contig 문자열 (예: 'B1-369/0 10-30')",
    )
    parser.add_argument(
        "--hotspot-res",
        default="",
        help="hotspot 잔기 목록 (쉼표 구분, 예: 'B122,B127,B184')",
    )
    parser.add_argument("--output-dir", required=True, help="출력 파일 저장 디렉토리")
    parser.add_argument("--seed", type=int, default=0, help="랜덤 시드")
    parser.add_argument("--num-designs", type=int, default=1, help="생성할 디자인 수")
    args = parser.parse_args()

    if args.input_json:
        global _tmp_receptor_file
        with open(args.input_json) as f:
            payload = json.load(f)

        # receptor_pdb / input_pdb: PDB 텍스트를 임시 파일에 기록
        receptor_pdb_text = payload.get("receptor_pdb") or payload.get("input_pdb", "")
        if receptor_pdb_text:
            _tmp_receptor_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".pdb", delete=False
            )
            _tmp_receptor_file.write(receptor_pdb_text)
            _tmp_receptor_file.flush()
            args.receptor_pdb = _tmp_receptor_file.name
        elif args.receptor_pdb is None:
            parser.error("--input-json의 receptor_pdb 키가 없고 --receptor-pdb도 지정되지 않음")

        args.contigs = payload.get("contigs", args.contigs)
        args.hotspot_res = payload.get("hotspot_res", args.hotspot_res or "")
        args.seed = int(payload.get("random_seed", payload.get("seed", args.seed)))
        args.num_designs = int(payload.get("num_designs", args.num_designs))

        if args.contigs is None:
            parser.error("--input-json의 contigs 키가 없고 --contigs도 지정되지 않음")
    else:
        if args.receptor_pdb is None:
            parser.error("--receptor-pdb 또는 --input-json 중 하나를 지정해야 합니다.")
        if args.contigs is None:
            parser.error("--contigs 또는 --input-json 중 하나를 지정해야 합니다.")

    return args


def _build_hydra_overrides(
    receptor_pdb: str,
    output_prefix: str,
    contigs: str,
    hotspot_res: "Union[str, List[str]]",
    seed: int,
    num_designs: int,
) -> List[str]:
    """Hydra override 인자 목록을 생성한다."""
    overrides = [
        f"inference.input_pdb={receptor_pdb}",
        f"inference.output_prefix={output_prefix}",
        f"contigmap.contigs=[{contigs}]",
        f"inference.num_designs={num_designs}",
        f"inference.deterministic=True",
        f"diffuser.T=50",
    ]
    # hotspot_res: list 또는 쉼표 구분 문자열 모두 허용
    if isinstance(hotspot_res, list):
        res_list = "[" + ",".join(str(r).strip() for r in hotspot_res) + "]"
    elif isinstance(hotspot_res, str) and hotspot_res:
        res_list = "[" + ",".join(r.strip() for r in hotspot_res.split(",")) + "]"
    else:
        res_list = ""
    if res_list:
        overrides.append(f"ppi.hotspot_res={res_list}")
    # RFdiffusion은 hydra config에 seed가 없음 — +로 추가
    overrides.append(f"+inference.seed={seed}")
    return overrides


def main() -> None:
    args = _parse_args()

    # 출력 디렉토리 준비
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_prefix = str(out_dir / f"backbone_seed{args.seed:04d}")

    # Hydra override 목록 구성
    overrides = _build_hydra_overrides(
        receptor_pdb=str(Path(args.receptor_pdb).resolve()),
        output_prefix=output_prefix,
        contigs=args.contigs,
        hotspot_res=args.hotspot_res,
        seed=args.seed,
        num_designs=args.num_designs,
    )

    cmd = [sys.executable, str(_INFERENCE_SCRIPT)] + overrides

    try:
        # stderr는 그대로 stderr로 흘려보내고 stdout은 캡처하지 않음
        # (hydra가 stdout에 로그를 출력할 수 있으므로 subprocess로 격리)
        result = subprocess.run(
            cmd,
            cwd=str(_RFDIFFUSION_REPO),
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(
            json.dumps({"error": f"RFdiffusion 실행 실패 (exit {exc.returncode})"}),
            flush=True,
        )
        sys.exit(1)

    # 생성된 PDB 파일 수집 (output_prefix*.pdb 패턴)
    generated_pdb_paths = sorted(glob.glob(f"{output_prefix}*.pdb"))
    if not generated_pdb_paths:
        print(
            json.dumps({"error": f"출력 PDB를 찾을 수 없음: {output_prefix}*.pdb"}),
            flush=True,
        )
        sys.exit(1)

    # PDB 파일 내용을 리스트로 읽음
    pdb_contents: List[str] = []
    for pdb_path in generated_pdb_paths:
        try:
            pdb_contents.append(Path(pdb_path).read_text(encoding="utf-8"))
        except OSError as exc:
            print(
                json.dumps({"error": f"PDB 파일 읽기 실패: {pdb_path} — {exc}"}),
                flush=True,
            )
            sys.exit(1)

    print(json.dumps({"output_pdbs": pdb_contents}), flush=True)

    # 임시 receptor PDB 파일 정리 (--input-json 모드)
    if _tmp_receptor_file is not None:
        try:
            Path(_tmp_receptor_file.name).unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    main()
