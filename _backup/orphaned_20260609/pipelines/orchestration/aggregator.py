from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from pipelines.shared.models import UnifiedCandidate


@dataclass(frozen=True)
class AggregatedResult:
    ranked: List[UnifiedCandidate]
    scores: Dict[str, float]


def _normalize(values: List[float]) -> List[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return [1.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def rank_fusion_weighted_sum(
    candidates: List[UnifiedCandidate],
    silo_weights: Dict[str, float],
) -> AggregatedResult:
    """Simple weighted rank fusion scaffold.

    - Uses each candidate's `raw_scores.unified_score` when available.
    - Applies per-silo weight from YAML policy.
    """
    base_scores = [float(c.raw_scores.get("unified_score", 0.0)) for c in candidates]
    norm_scores = _normalize(base_scores)

    fused_scores: Dict[str, float] = {}
    for cand, norm in zip(candidates, norm_scores):
        w = silo_weights.get(cand.silo.value.replace("silo_", "").upper(), 1.0)
        fused_scores[cand.id] = norm * w

    ranked = sorted(candidates, key=lambda c: fused_scores[c.id], reverse=True)
    return AggregatedResult(ranked=ranked, scores=fused_scores)
