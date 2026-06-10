"""SES (Screening Effectiveness Score) calculator.

Pure function — takes experiment results, returns a float [0.0, 1.0].
No I/O dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CandidateScore:
    """Minimal candidate representation for SES calculation."""
    candidate_id: str
    sequence: str
    ddg: float
    clash_score: float
    fwkt_conserved: bool  # F7-W8-K9-T10 all preserved
    cluster_id: Optional[str] = None


FWKT = "FWKT"  # pharmacophore positions 7-10
BASELINE_DDG = -48.438
DDG_GATE = -5.0
CLASH_GATE = 10.0


def is_hit(c: CandidateScore) -> bool:
    """Check if a candidate passes ALL gates."""
    return (
        c.ddg <= DDG_GATE
        and c.fwkt_conserved
        and c.clash_score <= CLASH_GATE
    )


def compute_ses(
    candidates: List[CandidateScore],
    first_hit_iter: int,
    max_iterations: int,
    repeat_best_ddgs: Optional[List[float]] = None,
    *,
    w_hit: float = 0.30,
    w_imp: float = 0.25,
    w_eff: float = 0.20,
    w_div: float = 0.15,
    w_rob: float = 0.10,
) -> dict:
    """Compute SES and its components.

    Args:
        candidates: All candidates from the experiment.
        first_hit_iter: Iteration number where first hit appeared (1-indexed).
        max_iterations: Total iterations in the experiment.
        repeat_best_ddgs: Best ddG values from repeated runs (for robustness).

    Returns:
        Dict with SES score and component breakdown.
    """
    hits = [c for c in candidates if is_hit(c)]
    n_total = len(candidates)

    # Hit Rate
    hit_rate = len(hits) / n_total if n_total > 0 else 0.0

    # Improvement
    best_ddg = min((c.ddg for c in candidates), default=0.0)
    improvement = max(0.0, (BASELINE_DDG - best_ddg) / abs(BASELINE_DDG))

    # Efficiency
    if first_hit_iter <= 0 or not hits:
        efficiency = 0.0
    else:
        efficiency = 1.0 - (first_hit_iter - 1) / max_iterations

    # Diversity
    if hits:
        clusters = set(c.cluster_id for c in hits if c.cluster_id)
        diversity = min(1.0, len(clusters) / len(hits)) if clusters else 0.0
    else:
        diversity = 0.0

    # Robustness
    if repeat_best_ddgs and len(repeat_best_ddgs) >= 2:
        import statistics
        mean_ddg = statistics.mean(repeat_best_ddgs)
        stdev_ddg = statistics.stdev(repeat_best_ddgs)
        cv = abs(stdev_ddg / mean_ddg) if mean_ddg != 0 else 1.0
        robustness = max(0.0, 1.0 - cv)
    else:
        robustness = 0.0  # cannot compute with single run

    ses = (
        w_hit * hit_rate
        + w_imp * improvement
        + w_eff * efficiency
        + w_div * diversity
        + w_rob * robustness
    )

    return {
        "ses": round(ses, 4),
        "hit_rate": round(hit_rate, 4),
        "improvement": round(improvement, 4),
        "efficiency": round(efficiency, 4),
        "diversity": round(diversity, 4),
        "robustness": round(robustness, 4),
        "n_hits": len(hits),
        "n_total": n_total,
        "best_ddg": round(best_ddg, 3),
    }
