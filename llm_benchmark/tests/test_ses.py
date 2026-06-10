"""Tests for SES (Screening Effectiveness Score) calculator."""
import pytest
from llm_benchmark.scoring.ses import CandidateScore, compute_ses, is_hit


def _make_candidate(ddg=-10.0, fwkt=True, clash=0.0, cluster="A", cid="c1", seq="AGCKNFFWKTFTSC"):
    return CandidateScore(
        candidate_id=cid, sequence=seq, ddg=ddg,
        clash_score=clash, fwkt_conserved=fwkt, cluster_id=cluster,
    )


class TestIsHit:
    def test_passes_all_gates(self):
        assert is_hit(_make_candidate(ddg=-10.0, fwkt=True, clash=5.0))

    def test_fails_ddg_gate(self):
        assert not is_hit(_make_candidate(ddg=-3.0))

    def test_fails_fwkt_gate(self):
        assert not is_hit(_make_candidate(fwkt=False))

    def test_fails_clash_gate(self):
        assert not is_hit(_make_candidate(clash=15.0))

    def test_boundary_ddg(self):
        assert is_hit(_make_candidate(ddg=-5.0))
        assert not is_hit(_make_candidate(ddg=-4.9))

    def test_boundary_clash(self):
        assert is_hit(_make_candidate(clash=10.0))
        assert not is_hit(_make_candidate(clash=10.1))


class TestComputeSES:
    def test_perfect_run(self):
        cands = [_make_candidate(ddg=-60.0, cluster=f"C{i}") for i in range(8)]
        result = compute_ses(cands, first_hit_iter=1, max_iterations=5,
                             repeat_best_ddgs=[-60.0, -59.5, -60.2])
        assert result["hit_rate"] == 1.0
        assert result["improvement"] > 0
        assert result["efficiency"] == 1.0
        assert result["ses"] > 0.5

    def test_zero_hits(self):
        cands = [_make_candidate(ddg=-2.0) for _ in range(4)]  # below gate
        result = compute_ses(cands, first_hit_iter=0, max_iterations=3)
        assert result["hit_rate"] == 0.0
        assert result["n_hits"] == 0
        assert result["efficiency"] == 0.0

    def test_empty_candidates(self):
        result = compute_ses([], first_hit_iter=0, max_iterations=3)
        assert result["hit_rate"] == 0.0
        assert result["ses"] == 0.0

    def test_robustness_single_run(self):
        cands = [_make_candidate()]
        result = compute_ses(cands, first_hit_iter=1, max_iterations=3)
        assert result["robustness"] == 0.0  # can't compute with 1 run

    def test_robustness_consistent(self):
        cands = [_make_candidate()]
        result = compute_ses(cands, first_hit_iter=1, max_iterations=3,
                             repeat_best_ddgs=[-50.0, -50.1, -49.9])
        assert result["robustness"] > 0.9  # very consistent

    def test_diversity_multiple_clusters(self):
        cands = [_make_candidate(cluster=f"C{i}", cid=f"c{i}") for i in range(4)]
        result = compute_ses(cands, first_hit_iter=1, max_iterations=3)
        assert result["diversity"] == 1.0  # 4 clusters / 4 hits

    def test_diversity_single_cluster(self):
        cands = [_make_candidate(cluster="A", cid=f"c{i}") for i in range(4)]
        result = compute_ses(cands, first_hit_iter=1, max_iterations=3)
        assert result["diversity"] == 0.25  # 1 cluster / 4 hits

    def test_efficiency_late_hit(self):
        cands = [_make_candidate()]
        result = compute_ses(cands, first_hit_iter=5, max_iterations=5)
        assert result["efficiency"] == 0.2  # 1 - 4/5

    def test_ses_weights_sum(self):
        # Default weights should sum to 1.0
        assert abs(0.30 + 0.25 + 0.20 + 0.15 + 0.10 - 1.0) < 1e-9
