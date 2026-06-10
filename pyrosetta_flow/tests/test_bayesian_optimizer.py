"""Tests for bayesian_optimizer module.

Covers:
- OneHotEmbedder encoding correctness
- Graceful degradation when botorch is unavailable
- fit -> suggest flow with mock data (botorch & fallback)
- Edge cases and error handling
"""
from __future__ import annotations

import importlib
import sys
import warnings
from typing import Dict, List
from unittest import mock

import numpy as np
import pytest

# We import from the module under test
from pyrosetta_flow.bayesian_optimizer import (
    AMINO_ACIDS,
    NUM_AA,
    SST14_SEQUENCE,
    BayesianPeptideOptimizer,
    OneHotEmbedder,
    PeptideEmbedder,
    _FallbackGP,
    _BOTORCH_AVAILABLE,
)


# =========================================================================
# OneHotEmbedder tests
# =========================================================================
class TestOneHotEmbedder:
    """Tests for the OneHotEmbedder fallback embedder."""

    def test_embed_shape_no_maxlen(self) -> None:
        """Output shape should be (len(seq) * 20,) without max_len."""
        emb = OneHotEmbedder()
        seq = "ACDE"
        result = emb.embed(seq)
        assert result.shape == (len(seq) * NUM_AA,)

    def test_embed_shape_with_maxlen(self) -> None:
        """Output shape should be (max_len * 20,) with max_len set."""
        emb = OneHotEmbedder(max_len=10)
        result = emb.embed("AC")
        assert result.shape == (10 * NUM_AA,)

    def test_embed_truncation(self) -> None:
        """Sequences longer than max_len should be truncated."""
        emb = OneHotEmbedder(max_len=3)
        result = emb.embed("ACDEFGHIK")
        assert result.shape == (3 * NUM_AA,)
        # First position should be Alanine
        assert result[0] == 1.0  # 'A' is index 0

    def test_one_hot_correctness(self) -> None:
        """Each residue should activate exactly one position."""
        emb = OneHotEmbedder()
        for aa in AMINO_ACIDS:
            vec = emb.embed(aa)
            assert vec.shape == (NUM_AA,)
            assert vec.sum() == 1.0
            expected_idx = AMINO_ACIDS.index(aa)
            assert vec[expected_idx] == 1.0

    def test_unknown_residue(self) -> None:
        """Unknown residues (e.g., 'X') should produce zero vectors."""
        emb = OneHotEmbedder()
        vec = emb.embed("X")
        assert vec.sum() == 0.0

    def test_embed_batch(self) -> None:
        """embed_batch should stack results."""
        emb = OneHotEmbedder(max_len=5)
        seqs = ["ACDEF", "GHIKL"]
        batch = emb.embed_batch(seqs)
        assert batch.shape == (2, 5 * NUM_AA)

    def test_lowercase_input(self) -> None:
        """Lowercase sequences should be handled (uppercased internally)."""
        emb = OneHotEmbedder()
        vec_lower = emb.embed("acde")
        vec_upper = emb.embed("ACDE")
        np.testing.assert_array_equal(vec_lower, vec_upper)

    def test_sst14_embedding(self) -> None:
        """SST-14 native sequence should embed correctly."""
        emb = OneHotEmbedder(max_len=14)
        vec = emb.embed(SST14_SEQUENCE)
        assert vec.shape == (14 * NUM_AA,)
        # 14 residues, each should have exactly one hot bit
        matrix = vec.reshape(14, NUM_AA)
        assert matrix.sum() == 14.0
        for row in matrix:
            assert row.sum() == 1.0


# =========================================================================
# PeptideEmbedder ABC tests
# =========================================================================
class TestPeptideEmbedderABC:
    """Test that PeptideEmbedder cannot be instantiated directly."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            PeptideEmbedder()  # type: ignore[abstract]


# =========================================================================
# _FallbackGP tests
# =========================================================================
class TestFallbackGP:
    """Tests for the numpy-only GP fallback."""

    def test_fit_predict(self) -> None:
        """Basic fit/predict should work."""
        gp = _FallbackGP(noise=1e-3)
        X = np.array([[0.0], [1.0], [2.0], [3.0]])
        y = np.array([0.0, 1.0, 4.0, 9.0])  # ~x^2
        gp.fit(X, y)
        mean, var = gp.predict(np.array([[1.0], [2.0]]))
        # Predictions at training points should be close to targets
        np.testing.assert_allclose(mean[0], 1.0, atol=0.2)
        np.testing.assert_allclose(mean[1], 4.0, atol=0.2)

    def test_predict_before_fit_raises(self) -> None:
        """Calling predict before fit should raise."""
        gp = _FallbackGP()
        with pytest.raises(AssertionError):
            gp.predict(np.array([[1.0]]))

    def test_variance_nonnegative(self) -> None:
        """Variance should always be non-negative."""
        gp = _FallbackGP()
        X = np.random.randn(10, 3)
        y = np.random.randn(10)
        gp.fit(X, y)
        _, var = gp.predict(np.random.randn(5, 3))
        assert np.all(var >= 0)


# =========================================================================
# Graceful degradation (botorch unavailable)
# =========================================================================
class TestGracefulDegradation:
    """Test behaviour when botorch/gpytorch are not installed."""

    def _make_optimizer_no_botorch(self) -> BayesianPeptideOptimizer:
        """Create an optimizer with _use_botorch forced to False."""
        emb = OneHotEmbedder(max_len=5)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            opt = BayesianPeptideOptimizer(
                embedder=emb,
                objectives=["score_a", "score_b"],
            )
        opt._use_botorch = False
        return opt

    def test_fallback_fit_suggest(self) -> None:
        """fit -> suggest flow should work with fallback GP."""
        opt = self._make_optimizer_no_botorch()
        candidates = [
            {"sequence": "ACDEF", "score_a": 1.0, "score_b": 2.0},
            {"sequence": "ACDEG", "score_a": 2.0, "score_b": 1.5},
            {"sequence": "ACDEH", "score_a": 0.5, "score_b": 3.0},
        ]
        opt.fit(candidates)
        assert opt.is_fitted

        suggestions = opt.suggest(n=3, reference_seq="ACDEF")
        assert len(suggestions) == 3
        for s in suggestions:
            assert "sequence" in s
            assert "position" in s
            assert "mutation" in s
            assert "acquisition_value" in s
            assert len(s["sequence"]) == 5

    def test_fallback_acquisition_values(self) -> None:
        """acquisition_values should return array with fallback GP."""
        opt = self._make_optimizer_no_botorch()
        candidates = [
            {"sequence": "ACDEF", "score_a": 1.0, "score_b": 2.0},
            {"sequence": "ACDEG", "score_a": 2.0, "score_b": 1.5},
        ]
        opt.fit(candidates)

        test_candidates = [
            {"sequence": "ACDEK"},
            {"sequence": "ACDEL"},
        ]
        acq = opt.acquisition_values(test_candidates)
        assert acq.shape == (2,)
        assert acq.dtype == np.float64 or acq.dtype == np.float32

    def test_warning_issued_when_no_botorch(self) -> None:
        """A warning should be issued when botorch is unavailable."""
        emb = OneHotEmbedder(max_len=5)
        # Patch the module-level flag
        import pyrosetta_flow.bayesian_optimizer as bo_mod

        original = bo_mod._BOTORCH_AVAILABLE
        try:
            bo_mod._BOTORCH_AVAILABLE = False
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                opt = BayesianPeptideOptimizer(
                    embedder=emb, objectives=["score"]
                )
                assert not opt._use_botorch
            warning_msgs = [str(x.message) for x in w]
            assert any("botorch" in msg.lower() for msg in warning_msgs)
        finally:
            bo_mod._BOTORCH_AVAILABLE = original


# =========================================================================
# Error handling
# =========================================================================
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_fit_empty_candidates(self) -> None:
        """fit with empty list should raise ValueError."""
        emb = OneHotEmbedder(max_len=5)
        opt = BayesianPeptideOptimizer(embedder=emb, objectives=["score"])
        opt._use_botorch = False
        with pytest.raises(ValueError, match="empty"):
            opt.fit([])

    def test_fit_missing_keys(self) -> None:
        """fit with missing objective keys should raise ValueError."""
        emb = OneHotEmbedder(max_len=5)
        opt = BayesianPeptideOptimizer(embedder=emb, objectives=["score"])
        opt._use_botorch = False
        with pytest.raises(ValueError, match="missing"):
            opt.fit([{"sequence": "ACDEF"}])

    def test_suggest_before_fit(self) -> None:
        """suggest before fit should raise RuntimeError."""
        emb = OneHotEmbedder(max_len=5)
        opt = BayesianPeptideOptimizer(embedder=emb, objectives=["score"])
        with pytest.raises(RuntimeError, match="fit"):
            opt.suggest(n=5, reference_seq="ACDEF")

    def test_acquisition_values_before_fit(self) -> None:
        """acquisition_values before fit should raise RuntimeError."""
        emb = OneHotEmbedder(max_len=5)
        opt = BayesianPeptideOptimizer(embedder=emb, objectives=["score"])
        with pytest.raises(RuntimeError, match="fit"):
            opt.acquisition_values([{"sequence": "ACDEF"}])


# =========================================================================
# Full flow with botorch (if available)
# =========================================================================
class TestWithBoTorch:
    """Tests that exercise the BoTorch path (skipped if unavailable)."""

    @pytest.mark.skipif(
        not _BOTORCH_AVAILABLE, reason="botorch not installed"
    )
    def test_botorch_fit_suggest(self) -> None:
        """Full BO flow: fit -> suggest with BoTorch backend."""
        emb = OneHotEmbedder(max_len=5)
        opt = BayesianPeptideOptimizer(
            embedder=emb,
            objectives=["binding", "stability"],
        )
        assert opt.has_botorch

        # Mock training data
        candidates = [
            {"sequence": "ACDEF", "binding": 0.8, "stability": 0.6},
            {"sequence": "ACDEG", "binding": 0.9, "stability": 0.5},
            {"sequence": "ACDEH", "binding": 0.7, "stability": 0.8},
            {"sequence": "ACDEK", "binding": 0.6, "stability": 0.9},
            {"sequence": "ACDEL", "binding": 0.85, "stability": 0.7},
        ]
        opt.fit(candidates)
        assert opt.is_fitted

        suggestions = opt.suggest(
            n=5, reference_seq="ACDEF", allowed_positions=[0, 2, 4]
        )
        assert len(suggestions) == 5
        for s in suggestions:
            assert "sequence" in s
            assert "acquisition_value" in s
            assert s["position"] in [0, 2, 4]

    @pytest.mark.skipif(
        not _BOTORCH_AVAILABLE, reason="botorch not installed"
    )
    def test_botorch_acquisition_values(self) -> None:
        """acquisition_values should return array with BoTorch backend."""
        emb = OneHotEmbedder(max_len=5)
        opt = BayesianPeptideOptimizer(
            embedder=emb,
            objectives=["score"],
        )
        candidates = [
            {"sequence": "ACDEF", "score": 1.0},
            {"sequence": "ACDEG", "score": 2.0},
            {"sequence": "ACDEH", "score": 0.5},
        ]
        opt.fit(candidates)

        test_cands = [{"sequence": "ACDEK"}, {"sequence": "ACDEL"}]
        acq = opt.acquisition_values(test_cands)
        assert acq.shape == (2,)

    @pytest.mark.skipif(
        not _BOTORCH_AVAILABLE, reason="botorch not installed"
    )
    def test_botorch_minimize_objective(self) -> None:
        """Minimization objectives should be handled correctly."""
        emb = OneHotEmbedder(max_len=5)
        opt = BayesianPeptideOptimizer(
            embedder=emb,
            objectives=["toxicity", "binding"],
            maximize=[False, True],  # minimize toxicity, maximize binding
        )
        candidates = [
            {"sequence": "ACDEF", "toxicity": 0.9, "binding": 0.8},
            {"sequence": "ACDEG", "toxicity": 0.1, "binding": 0.9},
            {"sequence": "ACDEH", "toxicity": 0.5, "binding": 0.7},
        ]
        opt.fit(candidates)
        suggestions = opt.suggest(n=3, reference_seq="ACDEF")
        assert len(suggestions) == 3


# =========================================================================
# Mutation enumeration tests
# =========================================================================
class TestMutationEnumeration:
    """Test the static mutation enumeration helper."""

    def test_enumerate_all_positions(self) -> None:
        """Should generate (seq_len * 19) mutations for all positions."""
        muts = BayesianPeptideOptimizer._enumerate_mutations("ACD")
        # 3 positions * 19 other AAs = 57
        assert len(muts) == 3 * 19

    def test_enumerate_allowed_positions(self) -> None:
        """Should only mutate allowed positions."""
        muts = BayesianPeptideOptimizer._enumerate_mutations(
            "ACD", allowed_positions=[0]
        )
        assert len(muts) == 19
        assert all(m["position"] == 0 for m in muts)

    def test_mutation_preserves_length(self) -> None:
        """Mutated sequences should have the same length as original."""
        muts = BayesianPeptideOptimizer._enumerate_mutations("ACDEF")
        for m in muts:
            assert len(m["sequence"]) == 5

    def test_mutation_differs_at_position(self) -> None:
        """Each mutation should differ from original at exactly one position."""
        ref = "ACDEF"
        muts = BayesianPeptideOptimizer._enumerate_mutations(ref)
        for m in muts:
            diffs = sum(1 for a, b in zip(ref, m["sequence"]) if a != b)
            assert diffs == 1

    def test_out_of_range_position_skipped(self) -> None:
        """Out-of-range positions should be silently skipped."""
        muts = BayesianPeptideOptimizer._enumerate_mutations(
            "ACD", allowed_positions=[100, -5]
        )
        assert len(muts) == 0
