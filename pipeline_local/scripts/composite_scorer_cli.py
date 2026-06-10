"""composite_scorer_cli.py
=========================
복합 스코어링 CLI 진입점 — A-04 action item.

사용법:
    # JSON 파일 입력
    python composite_scorer_cli.py --input candidates.json --output-dir runs_local/final_candidates/

    # CSV 파일 입력
    python composite_scorer_cli.py --input candidates.csv --output-dir runs_local/final_candidates/

    # 가중치 오버라이드 (JSON 문자열)
    python composite_scorer_cli.py --input candidates.json \\
        --weights '{"dg":0.4,"selectivity":0.3,"half_life":0.15,"admet_safety":0.1,"radiolysis_safety":0.05}'

    # Hard Cutoff 오버라이드
    python composite_scorer_cli.py --input candidates.json \\
        --hard-cutoffs '{"dg_max":-10.0,"selectivity_min":50.0}'

    # smoke test (내장 mock 데이터 실행)
    python composite_scorer_cli.py --smoke-test

    # P1 sprint wrapper enrichment
    python composite_scorer_cli.py --input candidates.csv --enrich-from-wrappers

출력 파일 (output-dir/ 하위):
    all_candidates.csv          — 전체 후보 결과
    hard_cutoff_pass.csv        — Hard Cutoff 통과 후보
    tier_s_candidates.csv       — Tier S 후보
    tier_a_candidates.csv       — Tier A 후보
    tier_b_candidates.csv       — Tier B 후보
    summary.json                — 요약 통계
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# sys.path 보정 (직접 실행 시 pipeline_local 패키지를 찾을 수 없는 경우 대비)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent        # pipeline_local/scripts/
_REPO_ROOT   = _SCRIPT_DIR.parent.parent              # SST14-M_scr/
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock 데이터 (smoke test 전용)
# ---------------------------------------------------------------------------
SMOKE_TEST_CANDIDATES: List[Dict[str, Any]] = [
    # dg 단위: REU (Rosetta Energy Units, more negative = stronger binding)
    # Hard Cutoff: dg ≤ -95.024 REU (SST14 ref), selectivity ≥ 100,
    #              radiolysis_count ≤ 3, admet_tox ≤ 0.3, instability_index < 40

    # Tier S/A/B 예상 후보 (Hard Cutoff 통과)
    {
        "candidate_id": "PRST-001",
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -105.5,          # < -95.024 → 통과
        "selectivity": 250.0,
        "half_life": 4.5,
        "admet_tox": 0.10,
        "radiolysis_count": 1,
        "instability_index": 28.5,
    },
    {
        "candidate_id": "PRST-002",
        "sequence": "AGCKNYFWKTFTSC",
        "dg": -101.8,
        "selectivity": 180.0,
        "half_life": 3.8,
        "admet_tox": 0.12,
        "radiolysis_count": 2,
        "instability_index": 30.1,
    },
    {
        "candidate_id": "PRST-003",
        "sequence": "AGCKNFFWKTFTAC",
        "dg": -99.2,
        "selectivity": 130.0,
        "half_life": 2.5,
        "admet_tox": 0.20,
        "radiolysis_count": 2,
        "instability_index": 35.0,
    },
    {
        "candidate_id": "PRST-004",
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -100.0,
        "selectivity": 200.0,
        "half_life": 2.0,
        "admet_tox": 0.25,
        "radiolysis_count": 2,
        "instability_index": 32.0,
    },
    {
        "candidate_id": "PRST-005",
        "sequence": "AGCKNFFAKTFTSC",
        "dg": -96.5,
        "selectivity": 105.0,
        "half_life": 1.2,
        "admet_tox": 0.28,
        "radiolysis_count": 1,
        "instability_index": 38.5,
    },
    {
        "candidate_id": "PRST-010",
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -97.8,
        "selectivity": 110.0,
        "half_life": 1.5,
        "admet_tox": 0.22,
        "radiolysis_count": 2,
        "instability_index": 36.0,
    },
    # FAIL 예상 후보들
    {
        "candidate_id": "PRST-006-FAIL-sel",  # 선택성 부족
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -100.0,
        "selectivity": 50.0,   # < 100 → FAIL
        "half_life": 3.0,
        "admet_tox": 0.15,
        "radiolysis_count": 2,
        "instability_index": 30.0,
    },
    {
        "candidate_id": "PRST-007-FAIL-admet",  # ADMET 실패
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -102.0,
        "selectivity": 200.0,
        "half_life": 3.5,
        "admet_tox": 0.45,   # > 0.3 → FAIL
        "radiolysis_count": 1,
        "instability_index": 28.0,
    },
    {
        "candidate_id": "PRST-008-FAIL-instab",  # 불안정
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -100.5,
        "selectivity": 150.0,
        "half_life": 2.5,
        "admet_tox": 0.18,
        "radiolysis_count": 2,
        "instability_index": 42.0,   # >= 40 → FAIL
    },
    {
        "candidate_id": "PRST-009-FAIL-radiolysis",  # Radiolysis 초과
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -101.5,
        "selectivity": 160.0,
        "half_life": 3.0,
        "admet_tox": 0.20,
        "radiolysis_count": 5,   # > 3 → FAIL
        "instability_index": 30.0,
    },
    # admet_tox 누락 케이스 (기본값 0.5 적용 → FAIL 예상)
    {
        "candidate_id": "PRST-011-missing-admet",
        "sequence": "AGCKNFFWKTFTSC",
        "dg": -100.0,
        "selectivity": 150.0,
        "half_life": 3.0,
        "radiolysis_count": 2,
        "instability_index": 30.0,
        # admet_tox 생략 → 기본값 0.5 (> 0.3 cutoff → FAIL)
    },
]


# ---------------------------------------------------------------------------
# 입력 로드
# ---------------------------------------------------------------------------

def load_candidates(input_path: str) -> List[Dict[str, Any]]:
    """JSON 또는 CSV 파일에서 후보 목록을 로드한다.

    Args:
        input_path: JSON (.json) 또는 CSV (.csv) 파일 경로.

    Returns:
        후보 list[dict].

    Raises:
        ValueError: 지원하지 않는 파일 형식.
        FileNotFoundError: 파일이 없을 때.
    """
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

    suffix = p.suffix.lower()
    if suffix == ".json":
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        # list[dict] 또는 {"candidates": [...]} 형식 지원
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "candidates" in data:
            return data["candidates"]
        else:
            raise ValueError(
                f"JSON 파일 형식 오류. list[dict] 또는 {{\"candidates\": [...]}} 형식이어야 합니다. "
                f"파일: {input_path}"
            )
    elif suffix in {".csv", ".tsv"}:
        try:
            import pandas as pd
            sep = "\t" if suffix == ".tsv" else ","
            df = pd.read_csv(p, sep=sep)
            return df.to_dict(orient="records")
        except ImportError:
            raise ImportError("CSV 입력은 pandas가 필요합니다. pip install pandas")
    else:
        raise ValueError(
            f"지원하지 않는 파일 형식: {suffix}. .json / .csv / .tsv 만 지원."
        )


# ---------------------------------------------------------------------------
# 요약 출력
# ---------------------------------------------------------------------------

def print_summary(df: "Any", verbose: bool = False) -> None:
    """스코어링 결과 요약을 stdout에 출력한다."""
    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        print("[ERROR] pandas 미설치")
        return

    if df is None or (hasattr(df, "empty") and df.empty):
        print("[WARNING] 결과 없음.")
        return

    tier_counts = df["tier"].value_counts().to_dict()
    print("\n" + "=" * 60)
    print("  복합 스코어링 결과 요약")
    print("=" * 60)
    print(f"  전체 후보: {len(df)}개")
    for tier in ["S", "A", "B", "FAIL"]:
        cnt = tier_counts.get(tier, 0)
        bar = "#" * cnt
        print(f"  Tier {tier:4s}: {cnt:3d}개  {bar}")
    print("=" * 60)

    if "fallback_admet_tox" in df.columns:
        fallback_df = df[df["fallback_admet_tox"].astype(bool)]
        if not fallback_df.empty:
            print("\n  [WARN] admet_tox wrapper fallback detected")
            cols = ["candidate_id", "admet_tox"]
            if "warnings" in fallback_df.columns:
                cols.append("warnings")
            print(fallback_df[cols].to_string(index=False))

    if verbose and "tier" in df.columns:
        # Tier S/A 후보 상세 출력
        top = df[df["tier"].isin(["S", "A"])][
            ["candidate_id", "tier", "wss", "pareto_rank", "dg", "selectivity",
             "half_life", "admet_tox", "radiolysis_count"]
        ]
        if not top.empty:
            print("\n  [Tier S/A 후보]")
            print(top.to_string(index=False))
    print()


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """CLI 메인 진입점.

    Returns:
        종료 코드 (0 = 성공, 1 = 에러).
    """
    parser = argparse.ArgumentParser(
        description="복합 스코어링 CLI — A-04 WSS + Pareto + Tier 분류",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="후보 입력 파일 경로 (.json 또는 .csv)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="결과 저장 디렉토리 (기본: runs_local/final_candidates/)",
    )
    parser.add_argument(
        "--weights", "-w",
        type=str,
        default=None,
        help=(
            "가중치 JSON 문자열 (예: "
            "'{\"dg\":0.4,\"selectivity\":0.3,\"half_life\":0.15,"
            "\"admet_safety\":0.1,\"radiolysis_safety\":0.05}')"
        ),
    )
    parser.add_argument(
        "--hard-cutoffs", "-c",
        type=str,
        default=None,
        help=(
            "Hard Cutoff JSON 문자열 (예: "
            "'{\"dg_max\":-10.0,\"selectivity_min\":50.0}')"
        ),
    )
    parser.add_argument(
        "--no-sst14-ref",
        action="store_true",
        default=False,
        help="pharmacology_guards.py에서 SST14 ref ΔG 자동 조회 비활성화",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        default=False,
        help="내장 mock 데이터로 smoke test 실행",
    )
    parser.add_argument(
        "--enrich-from-wrappers",
        action="store_true",
        default=False,
        help=(
            "P1 sprint wrappers로 sequence 기반 half_life/admet_tox 및 "
            "confidence metadata를 보강합니다. 기본값은 기존 입력/mock 유지."
        ),
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Tier S/A 후보 상세 출력",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨 (기본: INFO)",
    )

    args = parser.parse_args(argv)

    # 로깅 설정
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 가중치/Hard Cutoff 파싱
    weights: Optional[Dict[str, float]] = None
    if args.weights:
        try:
            weights = json.loads(args.weights)
        except json.JSONDecodeError as e:
            print(f"[ERROR] --weights JSON 파싱 실패: {e}", file=sys.stderr)
            return 1

    hard_cutoffs: Optional[Dict[str, Optional[float]]] = None
    if args.hard_cutoffs:
        try:
            hard_cutoffs = json.loads(args.hard_cutoffs)
        except json.JSONDecodeError as e:
            print(f"[ERROR] --hard-cutoffs JSON 파싱 실패: {e}", file=sys.stderr)
            return 1

    # 후보 로드
    if args.smoke_test:
        candidates = SMOKE_TEST_CANDIDATES
        print(f"[Smoke Test] 내장 mock 데이터 {len(candidates)}개 사용.")
    elif args.input:
        try:
            candidates = load_candidates(args.input)
            print(f"후보 {len(candidates)}개 로드: {args.input}")
        except (FileNotFoundError, ValueError, ImportError) as e:
            print(f"[ERROR] 입력 파일 로드 실패: {e}", file=sys.stderr)
            return 1
    else:
        print("[ERROR] --input 또는 --smoke-test 옵션이 필요합니다.", file=sys.stderr)
        parser.print_help()
        return 1

    # 스코어러 초기화 (sys.path 이미 보정됨)
    from pipeline_local.scripts.composite_scorer import CompositeScorer, WARN_LOW_PASSRATE

    scorer = CompositeScorer(
        weights=weights,
        hard_cutoffs=hard_cutoffs,
        use_sst14_ref_dg=not args.no_sst14_ref,
    )

    print(f"가중치: {scorer.weights}")
    print(f"Hard Cutoffs: {scorer.hard_cutoffs}")

    # 스코어링 실행
    try:
        df = scorer.score(candidates, enrich_from_wrappers=args.enrich_from_wrappers)
    except WARN_LOW_PASSRATE as e:
        print(f"[WARNING] Hard Cutoff 통과율 경고: {e}", file=sys.stderr)
        print("[WARNING] --hard-cutoffs 조정 후 재실행을 권고합니다.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] 스코어링 실패: {e}", file=sys.stderr)
        logger.exception("스코어링 실패")
        return 1

    # 요약 출력
    print_summary(df, verbose=args.verbose)

    # 결과 저장
    try:
        saved = scorer.save_results(df, output_dir=args.output_dir)
        for key, path in saved.items():
            print(f"  저장: [{key:20s}] {path}")
    except Exception as e:
        print(f"[ERROR] 결과 저장 실패: {e}", file=sys.stderr)
        logger.exception("결과 저장 실패")
        return 1

    # summary.json 저장
    if not df.empty:
        import pandas as pd
        tier_counts = df["tier"].value_counts().to_dict()
        summary = {
            "total_candidates": len(df),
            "tier_counts": tier_counts,
            "weights_used": scorer.weights,
            "hard_cutoffs_used": scorer.hard_cutoffs,
            "enrich_from_wrappers": bool(args.enrich_from_wrappers),
            "passrate": float(df["hard_cutoff_pass"].sum()) / len(df) if len(df) > 0 else 0.0,
        }
        out_dir = Path(args.output_dir) if args.output_dir else (
            Path(__file__).resolve().parent.parent.parent / "runs_local" / "final_candidates"
        )
        summary_path = out_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"  저장: [{'summary':20s}] {summary_path}")

    print("\n완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
