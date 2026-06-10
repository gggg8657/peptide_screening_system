import pytest

from pipelines.silo_a.src.config import ScoringConfig
from pipelines.silo_a.src.models import ArmName, CandidateRecord
from pipelines.silo_a.src.scoring import UnifiedScorer


def _scorer() -> UnifiedScorer:
    return UnifiedScorer(ScoringConfig())


def test_normalize_basic() -> None:
    s = _scorer()
    assert s.normalize(5.0, 0.0, 10.0) == pytest.approx(0.5)
    assert s.normalize(-5.0, -10.0, 0.0) == pytest.approx(0.5)
    assert s.normalize(20.0, 0.0, 10.0) == pytest.approx(1.0)


def test_score_arm1() -> None:
    s = _scorer()
    features = {"qed": 0.8, "dock_confidence": 0.6}
    score = s.score_candidate(features, ArmName.SMALL_MOL)
    assert 0.0 <= score <= 1.0
    assert score > 0.0


def test_rank_cross_arm() -> None:
    s = _scorer()
    candidates = [
        CandidateRecord("a", ArmName.SMALL_MOL, "CCO", "seed1", {"qed": 0.9, "dock_confidence": 0.7}),
        CandidateRecord("b", ArmName.DENOVO, "ACDE", "bb01", {"plddt": 85.0}),
        CandidateRecord("c", ArmName.FLEXPEP, "AGCKNFFWKTFTSC", "wt", {"delta_energy": -10.0}),
    ]
    ranked = s.rank_candidates(candidates)
    assert len(ranked) == 3
    assert ranked[0].rank == 1
    assert ranked[2].rank == 3
    assert all(r.score is not None for r in ranked)
