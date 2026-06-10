"""
stability_predictor/combined_report.py
========================================
Silo A + Silo B 결과 병합 + 정렬 리포트.

Usage:
    from pipeline_local.scripts.stability_predictor.combined_report import combine_silos

    silo_a_results = [...]  # List[SiloAStabilityResult]
    silo_b_results = [...]  # List[SiloBStabilityResult]

    report = combine_silos(silo_a_results, silo_b_results)
    # {
    #   "n_silo_a": int,
    #   "n_silo_b": int,
    #   "all_results": [...],
    #   "top_by_hl_score": [...],
    #   "top_stable": [...],
    #   "heuristic_disclaimer": str,
    # }

⚠️ HEURISTIC — hl_score_heuristic 기반 정렬은 임상 ranking 아님.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Union

from pipeline_local.scripts.stability_predictor.silo_a_evaluator import SiloAStabilityResult
from pipeline_local.scripts.stability_predictor.silo_b_evaluator import SiloBStabilityResult

_AnyResult = Union[SiloAStabilityResult, SiloBStabilityResult]

_HEURISTIC_DISCLAIMER = (
    "combine_silos 정렬 기준(hl_score_heuristic)은 임상 반감기 ranking이 아닌 "
    "in-silico heuristic score임. in-vitro serum stability assay 미수행."
)


def combine_silos(
    silo_a: List[SiloAStabilityResult],
    silo_b: List[SiloBStabilityResult],
    sort_by: str = "hl_score",
    top_n: int = 5,
) -> Dict[str, Any]:
    """Silo A + Silo B 결과 병합 및 통합 리포트 생성.

    Args:
        silo_a: Silo A 평가 결과 목록
        silo_b: Silo B 평가 결과 목록
        sort_by: 정렬 기준 ("hl_score" | "instability" | "mw")
        top_n: 상위 후보 N개 (top_by_hl_score / top_stable 각 N개)

    Returns:
        Dict with keys:
            n_silo_a, n_silo_b, n_total,
            all_results, top_by_hl_score, top_stable,
            summary, heuristic_disclaimer
    """
    all_results: List[_AnyResult] = list(silo_a) + list(silo_b)

    # 정렬
    if sort_by == "hl_score":
        sorted_results = sorted(
            all_results,
            key=lambda r: r.core.hl_score_heuristic,
            reverse=True,
        )
    elif sort_by == "instability":
        sorted_results = sorted(
            all_results,
            key=lambda r: (
                r.core.biophysical.instability_index
                if not math.isnan(r.core.biophysical.instability_index)
                else float("inf")
            ),
        )
    elif sort_by == "mw":
        sorted_results = sorted(
            all_results,
            key=lambda r: r.core.biophysical.mw,
        )
    else:
        sorted_results = all_results

    top_by_hl = sorted_results[:top_n]
    top_stable = [r for r in all_results if r.core.is_stable_biopython][:top_n]

    # 통계 요약
    mws = [r.core.biophysical.mw for r in all_results]
    gravys = [r.core.biophysical.gravy for r in all_results]
    instabs = [
        r.core.biophysical.instability_index
        for r in all_results
        if not math.isnan(r.core.biophysical.instability_index)
    ]
    hl_scores = [r.core.hl_score_heuristic for r in all_results if r.core.hl_score_heuristic > 0]

    def _mean(lst: List[float]) -> Optional[float]:
        return round(sum(lst) / len(lst), 4) if lst else None

    from typing import Optional  # local import to avoid circular at module level
    summary: Dict[str, Any] = {
        "n_stable_biopython": sum(1 for r in all_results if r.core.is_stable_biopython),
        "mean_mw": _mean(mws),
        "mean_gravy": _mean(gravys),
        "mean_instability": _mean(instabs),
        "mean_hl_score": _mean(hl_scores),
    }

    return {
        "n_silo_a": len(silo_a),
        "n_silo_b": len(silo_b),
        "n_total": len(all_results),
        "all_results": [r.to_dict() for r in all_results],
        "top_by_hl_score": [r.to_dict() for r in top_by_hl],
        "top_stable": [r.to_dict() for r in top_stable],
        "summary": summary,
        "heuristic_disclaimer": _HEURISTIC_DISCLAIMER,
    }
