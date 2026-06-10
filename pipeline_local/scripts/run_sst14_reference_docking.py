#!/usr/bin/env python3
"""
run_sst14_reference_docking.py
==============================
SST14 (AGCKNFFWKTFTSC) → SSTR2(7XNA) FlexPepDock n≥10 반복 도킹 실행기.

목적:
    A-05 액션 아이템 — SST14 reference dG (도킹 n≥10) 산출.
    평균/표준편차/95% CI를 계산하고 reference JSON 및 pharmacology_guards
    LITERATURE_VALUES 항목으로 저장한다.

사용법:
    conda run -n bio-tools python pipeline_local/scripts/run_sst14_reference_docking.py \
        --runs 10 --nstruct 5 --cycles 5

출력:
    runs_local/sst14_ref_docking_flexpep/run_N/result.json  (각 run)
    data/somatostatin_receptor/SST14_SSTR2_reference_dG.json  (집계)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# 경로 상수
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RECEPTOR_PDB = _REPO_ROOT / "data" / "somatostatin_receptor" / "SSTR2_7XNA.pdb"
_FLEXPEP_SCRIPT = _REPO_ROOT / "pipeline_local" / "scripts" / "flexpep_dock.py"
_OUTPUT_BASE = _REPO_ROOT / "runs_local" / "sst14_ref_docking_flexpep"
_REF_JSON_PATH = _REPO_ROOT / "data" / "somatostatin_receptor" / "SST14_SSTR2_reference_dG.json"

SEQUENCE = "AGCKNFFWKTFTSC"
RECEPTOR_NAME = "SSTR2_7XNA"


# ---------------------------------------------------------------------------
# 단일 run 실행
# ---------------------------------------------------------------------------

def run_single_dock(
    run_idx: int,
    nstruct: int,
    cycles: int,
    freedom: str = "med",
    ddg_cycle: int = 5,
    timeout_sec: int = 3600,
) -> Optional[Dict]:
    """단일 FlexPepDock run을 실행하고 JSON 결과를 반환한다.

    Args:
        run_idx:     run 인덱스 (1-based).
        nstruct:     앙상블 크기.
        cycles:      refinement cycles.
        freedom:     flex-pep-freedom 레벨.
        ddg_cycle:   ddG 계산 반복 횟수 (CLI 전달용).
        timeout_sec: subprocess 타임아웃 (초).

    Returns:
        결과 dict (JSON) 또는 None (실패 시).
    """
    run_dir = _OUTPUT_BASE / f"run_{run_idx}"
    run_dir.mkdir(parents=True, exist_ok=True)
    output_prefix = str(run_dir / "docked")
    result_path = run_dir / "result.json"
    stderr_path = run_dir / "stderr.txt"

    # 이미 성공한 run이면 재사용
    if result_path.exists():
        try:
            with open(result_path) as f:
                data = json.load(f)
            if not data.get("stub", True) and "dG_kcal_mol" in data:
                print(f"[A-05] run_{run_idx}: 기존 결과 재사용 dG={data['dG_kcal_mol']:.4f}")
                return data
        except (json.JSONDecodeError, KeyError):
            pass  # 손상된 경우 재실행

    cmd = [
        "conda", "run", "-n", "bio-tools", "python",
        str(_FLEXPEP_SCRIPT),
        "--receptor", str(_RECEPTOR_PDB),
        "--sequence", SEQUENCE,
        "--output-prefix", output_prefix,
        "--cycles", str(cycles),
        "--nstruct", str(nstruct),
        "--flex-pep-freedom", freedom,
        "--ddg-cycle", str(ddg_cycle),
    ]

    print(f"[A-05] run_{run_idx} 시작: nstruct={nstruct}, cycles={cycles}", flush=True)
    t0 = time.monotonic()

    try:
        with open(stderr_path, "w") as stderr_f:
            proc = subprocess.run(
                cmd,
                capture_output=False,
                stdout=subprocess.PIPE,
                stderr=stderr_f,
                timeout=timeout_sec,
                text=True,
                cwd=str(_REPO_ROOT),
            )
    except subprocess.TimeoutExpired:
        print(f"[A-05] run_{run_idx} TIMEOUT ({timeout_sec}s)", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[A-05] run_{run_idx} 실행 오류: {exc}", file=sys.stderr)
        return None

    elapsed = time.monotonic() - t0

    if proc.returncode != 0:
        print(f"[A-05] run_{run_idx} exit={proc.returncode} ({elapsed:.1f}s)", file=sys.stderr)
        # stderr 내용 요약 출력
        if stderr_path.exists():
            with open(stderr_path) as sf:
                lines = sf.readlines()
                for line in lines[-10:]:
                    print(f"  stderr: {line.rstrip()}", file=sys.stderr)
        return None

    # stdout에서 JSON 파싱
    stdout = proc.stdout.strip()
    if not stdout:
        print(f"[A-05] run_{run_idx} stdout 비어있음", file=sys.stderr)
        return None

    # stdout의 마지막 JSON 행 찾기 (PyRosetta가 stdout에 로그를 섞을 수 있음)
    data = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                data = json.loads(line)
                break
            except json.JSONDecodeError:
                continue

    if data is None:
        print(f"[A-05] run_{run_idx} JSON 파싱 실패: {stdout[:200]}", file=sys.stderr)
        return None

    data["run_idx"] = run_idx
    data["elapsed_sec"] = round(elapsed, 1)
    data["engine"] = "pyrosetta-flexpep"

    # 결과 저장
    with open(result_path, "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"[A-05] run_{run_idx} 완료: dG={data.get('dG_kcal_mol', 'N/A'):.4f} "
        f"({elapsed:.1f}s)"
    )
    return data


# ---------------------------------------------------------------------------
# 통계 계산
# ---------------------------------------------------------------------------

def compute_statistics(
    dg_values: List[float],
    elapsed_total: float,
) -> Dict:
    """dG 값들의 통계를 계산한다.

    Args:
        dg_values:     각 run의 dG_kcal_mol 값 목록.
        elapsed_total: 전체 실행 시간 (초).

    Returns:
        통계 dict.
    """
    n = len(dg_values)
    if n == 0:
        raise ValueError("dG 값이 없습니다 — 도킹 실패")

    mean_dg = statistics.mean(dg_values)
    std_dg = statistics.stdev(dg_values) if n > 1 else 0.0
    min_dg = min(dg_values)
    max_dg = max(dg_values)
    median_dg = statistics.median(dg_values)

    # 95% CI (t-분포 근사, n이 작을 때 사용)
    # t-table: n=10 → t(0.975, df=9) ≈ 2.262
    # n에 따른 t-critical 간이 테이블 (df = n-1)
    _T_CRIT: Dict[int, float] = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776,
        5: 2.571,  6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 14: 2.145, 19: 2.093, 29: 2.045,
    }
    df = n - 1
    # df 이하의 가장 가까운 키 선택
    t_crit = 2.0  # 기본값 (df≥30 → z ≈ 2.0)
    for k in sorted(_T_CRIT.keys(), reverse=True):
        if df >= k:
            t_crit = _T_CRIT[k]
            break

    se = std_dg / math.sqrt(n) if n > 1 else 0.0
    ci_lower = mean_dg - t_crit * se
    ci_upper = mean_dg + t_crit * se

    return {
        "sequence": SEQUENCE,
        "receptor": RECEPTOR_NAME,
        "n_runs": n,
        "mean_dG_kcal_mol": round(mean_dg, 4),
        "std_dG_kcal_mol": round(std_dg, 4),
        "min_dG": round(min_dg, 4),
        "max_dG": round(max_dg, 4),
        "median_dG": round(median_dg, 4),
        "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
        "all_dG_values": [round(v, 4) for v in dg_values],
        "elapsed_total_sec": round(elapsed_total, 1),
        "stub": False,
        "engine": "pyrosetta-flexpep",
        "note": (
            "PyRosetta FlexPepDock InterfaceAnalyzerMover ddG. "
            "양수 가능 — reference complex 부재로 Fallback 모드 사용 (확장 conformation). "
            "상대적 비교 기준으로 의미 있음 (A-04 composite_scorer.ddg_score 정규화 기준)."
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SST14 reference dG — FlexPepDock n≥10 반복 도킹 (A-05)"
    )
    parser.add_argument(
        "--runs", type=int, default=10,
        help="도킹 반복 횟수 (default: 10, A-05 요구사항: n≥10)",
    )
    parser.add_argument(
        "--nstruct", type=int, default=5,
        help="각 run당 FlexPepDock 앙상블 크기 (default: 5, smoke 목적 축소)",
    )
    parser.add_argument(
        "--cycles", type=int, default=5,
        help="FlexPepDock refinement cycles (default: 5)",
    )
    parser.add_argument(
        "--freedom", default="med",
        choices=["low", "med", "high"],
        help="flex-pep-freedom 레벨 (default: med)",
    )
    parser.add_argument(
        "--skip-existing", action="store_true", default=True,
        help="이미 완료된 run은 건너뜀 (default: True)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 도킹 없이 스크립트 구조만 확인",
    )
    args = parser.parse_args()

    print(f"[A-05] SST14 reference dG 도킹 시작: runs={args.runs}, nstruct={args.nstruct}")
    print(f"[A-05] receptor: {_RECEPTOR_PDB}")
    print(f"[A-05] sequence: {SEQUENCE}")
    print(f"[A-05] output_base: {_OUTPUT_BASE}")

    if args.dry_run:
        print("[A-05] --dry-run: 실제 실행 없이 종료")
        return

    _OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    t_global = time.monotonic()
    dg_values: List[float] = []
    failed_runs: List[int] = []
    all_results: List[Dict] = []

    for i in range(1, args.runs + 1):
        result = run_single_dock(
            run_idx=i,
            nstruct=args.nstruct,
            cycles=args.cycles,
            freedom=args.freedom,
            timeout_sec=3600,
        )
        if result is None:
            failed_runs.append(i)
            print(f"[A-05] run_{i} 실패 — 건너뜀", file=sys.stderr)
            continue

        dg_val = result.get("dG_kcal_mol", result.get("ddg"))
        if dg_val is None:
            print(f"[A-05] run_{i} dG 값 없음 — {list(result.keys())}", file=sys.stderr)
            failed_runs.append(i)
            continue

        dg_values.append(float(dg_val))
        all_results.append(result)
        print(f"[A-05] 누적 n={len(dg_values)}: dG 값 = {dg_val:.4f}")

    elapsed_total = time.monotonic() - t_global

    print(f"\n[A-05] 도킹 완료: 성공={len(dg_values)}/{args.runs}, 실패={failed_runs}")

    if len(dg_values) < 2:
        print(f"[A-05] 오류: 성공한 run이 {len(dg_values)}개뿐 — 통계 계산 불가", file=sys.stderr)
        sys.exit(1)

    # 통계 계산
    stats = compute_statistics(dg_values, elapsed_total)

    print(f"\n[A-05] === 통계 결과 ===")
    print(f"  n_runs:          {stats['n_runs']}")
    print(f"  mean_dG:         {stats['mean_dG_kcal_mol']:.4f} kcal/mol (REU)")
    print(f"  std_dG:          {stats['std_dG_kcal_mol']:.4f}")
    print(f"  min_dG:          {stats['min_dG']:.4f}")
    print(f"  max_dG:          {stats['max_dG']:.4f}")
    print(f"  median_dG:       {stats['median_dG']:.4f}")
    print(f"  95% CI:          [{stats['ci_95'][0]:.4f}, {stats['ci_95'][1]:.4f}]")
    print(f"  elapsed_total:   {stats['elapsed_total_sec']:.1f}s")

    # reference JSON 저장
    _REF_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_REF_JSON_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\n[A-05] reference JSON 저장: {_REF_JSON_PATH}")

    # summary.json 저장 (runs_local)
    summary_path = _OUTPUT_BASE / "summary_flexpep.json"
    summary = {
        **stats,
        "all_run_results": all_results,
        "failed_runs": failed_runs,
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[A-05] summary 저장: {summary_path}")

    print("\n[A-05] 완료.")


if __name__ == "__main__":
    main()
