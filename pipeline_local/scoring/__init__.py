"""pipeline_local.scoring
========================
Top-K 후보 선정 복합 스코어링 패키지 (A-04, KAERI-AIRL-MOM-2026-003).

Public API:
    radiolysis_scorer.compute_radiolysis_score  — Radiolysis 민감도 점수
    composite_scorer.score_candidates           — Hard Cutoff + WSS + Pareto + Tier
    composite_scorer.Tier                       — Tier 열거형 (S/A/B/FAIL)
    composite_scorer.ScoringResult              — 후보별 스코어링 결과 dataclass
"""

from pipeline_local.scoring.radiolysis_scorer import (
    RADIOLYSIS_SENSITIVITY,
    HARD_CUTOFF_SENSITIVE_COUNT,
    compute_radiolysis_score,
    passes_hard_cutoff,
)
from pipeline_local.scoring.composite_scorer import (
    Tier,
    ScoringResult,
    WSS_WEIGHTS,
    score_candidates,
    apply_hard_cutoffs,
    compute_wss,
)

__all__ = [
    # radiolysis
    "RADIOLYSIS_SENSITIVITY",
    "HARD_CUTOFF_SENSITIVE_COUNT",
    "compute_radiolysis_score",
    "passes_hard_cutoff",
    # composite
    "Tier",
    "ScoringResult",
    "WSS_WEIGHTS",
    "score_candidates",
    "apply_hard_cutoffs",
    "compute_wss",
]
