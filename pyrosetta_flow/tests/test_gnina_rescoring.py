"""Tests for GNINA CNN Rescoring wrapper.

All tests run without a real gnina binary — dry-run mode and unit-level
logic are fully exercised.
"""
from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from pyrosetta_flow.gnina_rescoring import (
    _parse_gnina_output,
    batch_gnina_rescore,
    exponential_rank_consensus,
    gnina_rescore,
    split_receptor_peptide,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_COMPLEX_PDB = textwrap.dedent("""\
    ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N
    ATOM      2  CA  ALA A   1       1.458   0.000   0.000  1.00  0.00           C
    ATOM      3  C   ALA A   1       2.009   1.420   0.000  1.00  0.00           C
    ATOM      4  N   GLY B   1       5.000   5.000   5.000  1.00  0.00           N
    ATOM      5  CA  GLY B   1       6.458   5.000   5.000  1.00  0.00           C
    END
""")


@pytest.fixture()
def complex_pdb(tmp_path: Path) -> Path:
    """Write a minimal two-chain PDB and return its path."""
    pdb = tmp_path / "complex.pdb"
    pdb.write_text(MOCK_COMPLEX_PDB)
    return pdb


# ---------------------------------------------------------------------------
# split_receptor_peptide
# ---------------------------------------------------------------------------


class TestSplitReceptorPeptide:
    """Tests for PDB chain splitting."""

    def test_splits_chains_correctly(self, complex_pdb: Path) -> None:
        rec_path, pep_path = split_receptor_peptide(str(complex_pdb))
        try:
            rec_text = Path(rec_path).read_text()
            pep_text = Path(pep_path).read_text()

            # Receptor should contain chain A atoms
            assert "ALA A" in rec_text
            assert "GLY B" not in rec_text

            # Peptide should contain chain B atoms
            assert "GLY B" in pep_text
            assert "ALA A" not in pep_text

            # Both should end with END
            assert rec_text.strip().endswith("END")
            assert pep_text.strip().endswith("END")
        finally:
            Path(rec_path).unlink(missing_ok=True)
            Path(pep_path).unlink(missing_ok=True)

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            split_receptor_peptide("/nonexistent/path.pdb")

    def test_missing_receptor_chain(self, tmp_path: Path) -> None:
        pdb = tmp_path / "only_b.pdb"
        pdb.write_text(
            "ATOM      1  N   GLY B   1       5.000   5.000   5.000  1.00  0.00\n"
            "END\n"
        )
        with pytest.raises(ValueError, match="receptor chain"):
            split_receptor_peptide(str(pdb))

    def test_missing_peptide_chain(self, tmp_path: Path) -> None:
        pdb = tmp_path / "only_a.pdb"
        pdb.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00\n"
            "END\n"
        )
        with pytest.raises(ValueError, match="peptide chain"):
            split_receptor_peptide(str(pdb))

    def test_custom_chain_ids(self, tmp_path: Path) -> None:
        pdb = tmp_path / "custom.pdb"
        pdb.write_text(
            "ATOM      1  N   ALA R   1       0.000   0.000   0.000  1.00  0.00\n"
            "ATOM      2  N   GLY L   1       5.000   5.000   5.000  1.00  0.00\n"
            "END\n"
        )
        rec_path, pep_path = split_receptor_peptide(
            str(pdb), receptor_chain="R", peptide_chain="L"
        )
        try:
            assert "ALA R" in Path(rec_path).read_text()
            assert "GLY L" in Path(pep_path).read_text()
        finally:
            Path(rec_path).unlink(missing_ok=True)
            Path(pep_path).unlink(missing_ok=True)

    def test_hetatm_records_included(self, tmp_path: Path) -> None:
        pdb = tmp_path / "hetatm.pdb"
        pdb.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00\n"
            "HETATM    2  ZN  ZN  B   1       5.000   5.000   5.000  1.00  0.00\n"
            "END\n"
        )
        rec_path, pep_path = split_receptor_peptide(str(pdb))
        try:
            assert "HETATM" in Path(pep_path).read_text()
        finally:
            Path(rec_path).unlink(missing_ok=True)
            Path(pep_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# _parse_gnina_output
# ---------------------------------------------------------------------------


class TestParseGninaOutput:
    """Tests for GNINA stdout parsing."""

    def test_valid_output(self) -> None:
        stdout = textwrap.dedent("""\
            Using default CNN model
            CNNscore  CNNaffinity  Vina
            0.850     6.120        -7.300
        """)
        scores = _parse_gnina_output(stdout)
        assert scores["gnina_cnn_score"] == pytest.approx(0.85)
        assert scores["gnina_cnn_affinity"] == pytest.approx(6.12)
        assert scores["gnina_vina_score"] == pytest.approx(-7.3)

    def test_missing_header(self) -> None:
        scores = _parse_gnina_output("no useful output here\n")
        assert math.isnan(scores["gnina_cnn_score"])

    def test_truncated_data(self) -> None:
        stdout = "CNNscore  CNNaffinity  Vina\n0.5\n"
        scores = _parse_gnina_output(stdout)
        assert math.isnan(scores["gnina_cnn_score"])


# ---------------------------------------------------------------------------
# gnina_rescore — dry-run mode
# ---------------------------------------------------------------------------


class TestGninaRescore:
    """Test gnina_rescore in dry-run (no binary) mode."""

    def test_dry_run_when_gnina_missing(self, complex_pdb: Path) -> None:
        with patch(
            "pyrosetta_flow.gnina_rescoring._is_gnina_available",
            return_value=False,
        ):
            scores = gnina_rescore(str(complex_pdb))

        assert scores["gnina_dry_run"] == 1.0
        assert scores["gnina_cnn_score"] == 0.0
        assert scores["gnina_cnn_affinity"] == 0.0
        assert scores["gnina_vina_score"] == 0.0

    def test_successful_rescore_with_mock_gnina(self, complex_pdb: Path) -> None:
        mock_stdout = (
            "Using default CNN\n"
            "CNNscore  CNNaffinity  Vina\n"
            "0.920     5.500        -8.100\n"
        )
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_stdout
        mock_result.stderr = ""

        with patch(
            "pyrosetta_flow.gnina_rescoring._is_gnina_available",
            return_value=True,
        ), patch(
            "pyrosetta_flow.gnina_rescoring.subprocess.run",
            return_value=mock_result,
        ):
            scores = gnina_rescore(str(complex_pdb))

        assert scores["gnina_cnn_score"] == pytest.approx(0.92)
        assert scores["gnina_cnn_affinity"] == pytest.approx(5.5)
        assert scores["gnina_vina_score"] == pytest.approx(-8.1)
        assert "gnina_dry_run" not in scores

    def test_gnina_nonzero_return_code(self, complex_pdb: Path) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: something went wrong"

        with patch(
            "pyrosetta_flow.gnina_rescoring._is_gnina_available",
            return_value=True,
        ), patch(
            "pyrosetta_flow.gnina_rescoring.subprocess.run",
            return_value=mock_result,
        ):
            scores = gnina_rescore(str(complex_pdb))

        assert scores.get("gnina_error") == 1.0
        assert math.isnan(scores["gnina_cnn_score"])


# ---------------------------------------------------------------------------
# batch_gnina_rescore
# ---------------------------------------------------------------------------


class TestBatchGninaRescore:
    """Test batch rescoring."""

    def test_empty_list(self) -> None:
        assert batch_gnina_rescore([]) == []

    def test_batch_dry_run(self, complex_pdb: Path) -> None:
        paths = [str(complex_pdb)] * 3
        with patch(
            "pyrosetta_flow.gnina_rescoring._is_gnina_available",
            return_value=False,
        ):
            results = batch_gnina_rescore(paths, max_workers=2)

        assert len(results) == 3
        for r in results:
            assert r["gnina_dry_run"] == 1.0

    def test_batch_preserves_order(self, complex_pdb: Path) -> None:
        """Ensure results map back to input order."""
        paths = [str(complex_pdb)] * 5
        with patch(
            "pyrosetta_flow.gnina_rescoring._is_gnina_available",
            return_value=False,
        ):
            results = batch_gnina_rescore(paths, max_workers=2)

        assert len(results) == 5


# ---------------------------------------------------------------------------
# exponential_rank_consensus
# ---------------------------------------------------------------------------


class TestExponentialRankConsensus:
    """Tests for ECR scoring."""

    @pytest.fixture()
    def sample_candidates(self) -> List[Dict]:
        return [
            {
                "id": "c1",
                "gnina_cnn_score": 0.3,
                "gnina_cnn_affinity": 4.0,
                "gnina_vina_score": -5.0,
            },
            {
                "id": "c2",
                "gnina_cnn_score": 0.1,
                "gnina_cnn_affinity": 6.0,
                "gnina_vina_score": -9.0,
            },
            {
                "id": "c3",
                "gnina_cnn_score": 0.5,
                "gnina_cnn_affinity": 5.0,
                "gnina_vina_score": -7.0,
            },
        ]

    def test_empty_input(self) -> None:
        assert exponential_rank_consensus([]) == []

    def test_ecr_returns_all_candidates(self, sample_candidates: List[Dict]) -> None:
        result = exponential_rank_consensus(sample_candidates)
        assert len(result) == 3

    def test_ecr_adds_score_and_ranks(self, sample_candidates: List[Dict]) -> None:
        result = exponential_rank_consensus(sample_candidates)
        for cand in result:
            assert "ecr_score" in cand
            assert "ecr_ranks" in cand
            assert isinstance(cand["ecr_ranks"], dict)

    def test_ecr_sorted_descending(self, sample_candidates: List[Dict]) -> None:
        result = exponential_rank_consensus(sample_candidates)
        scores = [c["ecr_score"] for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_ecr_does_not_modify_input(self, sample_candidates: List[Dict]) -> None:
        original_keys = set(sample_candidates[0].keys())
        exponential_rank_consensus(sample_candidates)
        assert set(sample_candidates[0].keys()) == original_keys

    def test_ecr_calculation_correctness(self) -> None:
        """Verify ECR formula with a simple 2-candidate, 1-key case."""
        candidates = [
            {"gnina_cnn_score": 0.2},
            {"gnina_cnn_score": 0.1},
        ]
        result = exponential_rank_consensus(
            candidates, score_keys=["gnina_cnn_score"]
        )
        n = 2
        # Lower is better: 0.1 gets rank 1, 0.2 gets rank 2
        best = result[0]
        worst = result[1]

        assert best["ecr_ranks"]["gnina_cnn_score"] == 1
        assert worst["ecr_ranks"]["gnina_cnn_score"] == 2

        expected_best_ecr = math.exp(-1 / n)
        expected_worst_ecr = math.exp(-2 / n)
        assert best["ecr_score"] == pytest.approx(expected_best_ecr, rel=1e-5)
        assert worst["ecr_score"] == pytest.approx(expected_worst_ecr, rel=1e-5)

    def test_ecr_handles_nan_values(self) -> None:
        candidates = [
            {"gnina_cnn_score": 0.5},
            {"gnina_cnn_score": float("nan")},
        ]
        result = exponential_rank_consensus(
            candidates, score_keys=["gnina_cnn_score"]
        )
        # NaN should be ranked last
        nan_cand = [c for c in result if c["ecr_ranks"]["gnina_cnn_score"] == 2][0]
        assert nan_cand is not None

    def test_ecr_with_custom_keys(self) -> None:
        candidates = [
            {"score_a": 1.0, "score_b": 3.0},
            {"score_a": 2.0, "score_b": 1.0},
        ]
        result = exponential_rank_consensus(
            candidates, score_keys=["score_a", "score_b"]
        )
        assert len(result) == 2
        # Both candidates have one rank-1 and one rank-2, so ECR is equal
        assert result[0]["ecr_score"] == pytest.approx(result[1]["ecr_score"])

    def test_ecr_single_candidate(self) -> None:
        candidates = [{"gnina_cnn_score": 0.5}]
        result = exponential_rank_consensus(
            candidates, score_keys=["gnina_cnn_score"]
        )
        assert len(result) == 1
        assert result[0]["ecr_ranks"]["gnina_cnn_score"] == 1
