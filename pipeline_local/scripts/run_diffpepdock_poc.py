#!/usr/bin/env python3
"""
run_diffpepdock_poc.py
======================
A-06 DiffPepDock PoC 실행 스크립트.

DiffPepDock (DiffPepBuilder 기반 protein-peptide docking 모듈)을
SSTR2 수용체 + SST14 펩타이드에 적용하여 도킹 포즈를 생성하고
타이밍·GPU 사용량을 기록한다.

사용법:
    conda run -n diffpepbuilder python pipeline_local/scripts/run_diffpepdock_poc.py \
        --num-poses 10 --output-dir runs_local/diffdock_poc

출력:
    - runs_local/diffdock_poc/poses/  : 생성된 PDB 파일들
    - runs_local/diffdock_poc/poc_report.json : 타이밍/GPU/포즈 수 기록
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DIFFPEP_ROOT = _REPO_ROOT / "local_models" / "DiffPepBuilder"
_DEFAULT_OUTPUT = _REPO_ROOT / "runs_local" / "diffdock_poc"
_RECEPTOR_PDB = _REPO_ROOT / "runs_local" / "diffdock_poc" / "data" / "SSTR2receptor.pdb"
_METADATA_CSV = _REPO_ROOT / "runs_local" / "diffdock_poc" / "processed" / "metadata_test.csv"
_CHECKPOINT = _DIFFPEP_ROOT / "experiments" / "checkpoints" / "diffpepdock_v1.pth"


def _gpu_memory_mb(device_idx: int = 2) -> Optional[float]:
    """nvidia-smi로 GPU 사용 메모리(MB) 조회."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits",
             f"--id={device_idx}"],
            capture_output=True, text=True, timeout=10
        )
        val = result.stdout.strip().split("\n")[0]
        return float(val)
    except Exception:
        return None


def _gpu_total_mb(device_idx: int = 2) -> Optional[float]:
    """nvidia-smi로 GPU 전체 메모리(MB) 조회."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits",
             f"--id={device_idx}"],
            capture_output=True, text=True, timeout=10
        )
        val = result.stdout.strip().split("\n")[0]
        return float(val)
    except Exception:
        return None


def run_diffpepdock(
    num_poses: int,
    output_dir: Path,
    gpu_id: int = 2,
) -> Dict[str, Any]:
    """
    DiffPepDock 추론 실행.

    Parameters
    ----------
    num_poses : int
        생성할 도킹 포즈 수
    output_dir : Path
        결과 저장 디렉터리
    gpu_id : int
        사용할 CUDA 장치 인덱스

    Returns
    -------
    dict
        타이밍, GPU, 포즈 경로 등 결과 메타데이터
    """
    output_dir = Path(output_dir)
    poses_dir = output_dir / "poses"
    poses_dir.mkdir(parents=True, exist_ok=True)

    # DiffPepDock 실행 디렉터리 (BASE_PATH 기준)
    run_dir = _DIFFPEP_ROOT / "runs" / "docking"

    # 환경 변수 설정
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    env["BASE_PATH"] = str(_DIFFPEP_ROOT)
    env["PYTHONPATH"] = str(_DIFFPEP_ROOT)

    # GPU 메모리 (실행 전)
    gpu_before_mb = _gpu_memory_mb(gpu_id)
    gpu_total_mb = _gpu_total_mb(gpu_id)

    # torchrun 단일 GPU로 실행
    cmd = [
        sys.executable,  # conda env 내 python
        "-m", "torchrun",
        "--nproc-per-node=1",
        str(_DIFFPEP_ROOT / "experiments" / "run_docking.py"),
        f"data.val_csv_path={str(_METADATA_CSV)}",
        f"data.num_repeat_per_eval_sample={num_poses}",
        f"experiment.num_gpus=1",
        "experiment.use_ddp=False",
        "postprocess.run_postprocess=False",
        "postprocess.amber_relax=False",
        "postprocess.rosetta_relax=False",
        f"experiment.eval_dir={str(run_dir)}",
    ]

    start_time = time.time()
    print(f"[DiffPepDock] Running {num_poses} poses on GPU {gpu_id}...")
    print(f"[DiffPepDock] CMD: {' '.join(cmd)}")

    proc = subprocess.run(
        cmd,
        cwd=str(_DIFFPEP_ROOT),
        env=env,
        capture_output=False,
        timeout=3600,
    )
    elapsed = time.time() - start_time

    # GPU 메모리 (실행 후)
    gpu_after_mb = _gpu_memory_mb(gpu_id)

    # 생성된 PDB 수집
    generated_pdbs = sorted(run_dir.rglob("*.pdb")) if run_dir.exists() else []

    # poses/ 디렉터리로 복사
    copied = []
    for i, pdb in enumerate(generated_pdbs):
        dest = poses_dir / f"pose_{i:03d}_{pdb.name}"
        shutil.copy2(pdb, dest)
        copied.append(str(dest))

    return {
        "success": proc.returncode == 0,
        "returncode": proc.returncode,
        "num_poses_requested": num_poses,
        "num_poses_generated": len(generated_pdbs),
        "pose_paths": copied,
        "elapsed_sec": round(elapsed, 2),
        "gpu_id": gpu_id,
        "gpu_memory_before_mb": gpu_before_mb,
        "gpu_memory_after_mb": gpu_after_mb,
        "gpu_total_mb": gpu_total_mb,
        "gpu_memory_used_mb": (
            round(gpu_after_mb - (gpu_before_mb or 0), 1)
            if gpu_after_mb and gpu_before_mb else None
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DiffPepDock PoC runner for SSTR2+SST14")
    p.add_argument("--num-poses", type=int, default=10, help="Number of docking poses")
    p.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT, help="Output directory")
    p.add_argument("--gpu-id", type=int, default=2, help="CUDA device index")
    return p


def main() -> None:
    args = build_parser().parse_args()

    if not _CHECKPOINT.exists():
        print(f"[ERROR] DiffPepDock checkpoint not found: {_CHECKPOINT}", file=sys.stderr)
        sys.exit(1)

    if not _METADATA_CSV.exists():
        print(f"[ERROR] Preprocessed metadata CSV not found: {_METADATA_CSV}", file=sys.stderr)
        print("[INFO] Run process_batch_dock.py first.", file=sys.stderr)
        sys.exit(1)

    result = run_diffpepdock(
        num_poses=args.num_poses,
        output_dir=args.output_dir,
        gpu_id=args.gpu_id,
    )

    report_path = Path(args.output_dir) / "poc_report.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n[DiffPepDock] Completed in {result['elapsed_sec']:.1f}s")
    print(f"[DiffPepDock] Poses generated: {result['num_poses_generated']}")
    print(f"[DiffPepDock] Report: {report_path}")

    if not result["success"]:
        print(f"[DiffPepDock] WARNING: returncode={result['returncode']}", file=sys.stderr)
        sys.exit(result["returncode"])


if __name__ == "__main__":
    main()
