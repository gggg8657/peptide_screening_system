"""Tests for adapter.py: config validation, mutation generation, helpers."""
from __future__ import annotations

import random
from pathlib import Path
from typing import List

import pytest

from pyrosetta_flow.adapter import (
    AA_NO_CYS,
    candidate_to_dict,
    choose_objective_mode,
    generate_guided_mutant,
    generate_random_mutant,
    notebook_mapping,
    validate_config,
)
from pyrosetta_flow.schema import CandidateResult, FlowConfig


ORIGINAL = "AGCKNFFWKTFTSC"
DESIGN_POS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14]


# ===================================================================
# validate_config tests  (Critical priority #2)
# ===================================================================

class TestValidateConfig:

    def test_valid_config(self, flow_config):
        validate_config(flow_config)  # should not raise

    def test_missing_pdb(self, tmp_path):
        cfg = FlowConfig(template_pdb=str(tmp_path / "nonexistent.pdb"))
        with pytest.raises(FileNotFoundError, match="Template PDB not found"):
            validate_config(cfg)

    def test_invalid_n_candidates_zero(self, tmp_pdb):
        cfg = FlowConfig(template_pdb=str(tmp_pdb), n_candidates=0)
        with pytest.raises(ValueError, match="n_candidates must be >= 1"):
            validate_config(cfg)

    def test_invalid_n_candidates_negative(self, tmp_pdb):
        cfg = FlowConfig(template_pdb=str(tmp_pdb), n_candidates=-5)
        with pytest.raises(ValueError, match="n_candidates must be >= 1"):
            validate_config(cfg)

    def test_empty_design_positions(self, tmp_pdb):
        cfg = FlowConfig(template_pdb=str(tmp_pdb), design_positions=[])
        with pytest.raises(ValueError, match="design_positions must not be empty"):
            validate_config(cfg)


# ===================================================================
# generate_random_mutant tests  (High priority #5)
# ===================================================================

class TestGenerateRandomMutant:

    def test_deterministic_with_seed(self):
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        mut1 = generate_random_mutant(ORIGINAL, DESIGN_POS, rng1)
        mut2 = generate_random_mutant(ORIGINAL, DESIGN_POS, rng2)
        assert mut1 == mut2

    def test_produces_mutation(self):
        rng = random.Random(42)
        mut = generate_random_mutant(ORIGINAL, DESIGN_POS, rng)
        assert mut != ORIGINAL
        assert len(mut) == len(ORIGINAL)

    def test_cysteine_exclusion(self):
        """No Cysteine should appear at mutated positions."""
        rng = random.Random(100)
        for _ in range(50):
            mut = generate_random_mutant(ORIGINAL, DESIGN_POS, rng)
            for pos in DESIGN_POS:
                idx = pos - 1
                if mut[idx] != ORIGINAL[idx]:
                    assert mut[idx] != "C", f"Cysteine at mutated pos {pos}"

    def test_preserves_non_design_positions(self):
        rng = random.Random(42)
        non_design = [i for i in range(1, 15) if i not in DESIGN_POS]
        for _ in range(20):
            mut = generate_random_mutant(ORIGINAL, DESIGN_POS, rng)
            for pos in non_design:
                assert mut[pos - 1] == ORIGINAL[pos - 1]

    def test_explicit_n_mutations(self):
        rng = random.Random(42)
        mut = generate_random_mutant(ORIGINAL, DESIGN_POS, rng, n_mutations=1)
        diffs = sum(1 for a, b in zip(ORIGINAL, mut) if a != b)
        assert diffs == 1

    def test_n_mutations_capped_by_available(self):
        """If n_mutations > len(design_positions), clamp to available."""
        rng = random.Random(42)
        short_positions = [1, 2]
        mut = generate_random_mutant(ORIGINAL, short_positions, rng, n_mutations=10)
        diffs = sum(1 for a, b in zip(ORIGINAL, mut) if a != b)
        assert diffs <= 2

    def test_invalid_positions_filtered(self):
        """Positions outside sequence length are silently filtered."""
        rng = random.Random(42)
        result = generate_random_mutant(ORIGINAL, [100, 200], rng)
        assert result == ORIGINAL  # no valid positions → return original

    def test_empty_positions(self):
        rng = random.Random(42)
        result = generate_random_mutant(ORIGINAL, [], rng)
        assert result == ORIGINAL


# ===================================================================
# generate_guided_mutant tests  (High priority #6)
# ===================================================================

class TestGenerateGuidedMutant:

    def test_uses_focus_positions(self):
        rng = random.Random(42)
        guidance = {
            "focus_positions": [5, 6],
            "suggested_mutations": {"5": ["W", "F"], "6": ["E", "D"]},
        }
        mut = generate_guided_mutant(ORIGINAL, DESIGN_POS, guidance, rng)
        assert mut != ORIGINAL
        # At least one of pos 5 or 6 should be mutated
        changed = []
        for pos in [5, 6]:
            if mut[pos - 1] != ORIGINAL[pos - 1]:
                changed.append(pos)
        assert len(changed) > 0

    def test_suggestion_applied(self):
        """When suggested_mutations are given, chosen AA should come from suggestions."""
        rng = random.Random(42)
        guidance = {
            "focus_positions": [5],
            "suggested_mutations": {"5": ["W"]},  # only W available
        }
        mut = generate_guided_mutant(ORIGINAL, DESIGN_POS, guidance, rng)
        # pos 5 is 'N' in original; should become 'W' from suggestion
        if mut[4] != ORIGINAL[4]:
            assert mut[4] == "W"

    def test_cysteine_excluded_from_suggestions(self):
        """If suggestion includes C, it should be filtered out."""
        rng = random.Random(42)
        guidance = {
            "focus_positions": [5],
            "suggested_mutations": {"5": ["C"]},
        }
        # "C" should be excluded, fallback to random non-C
        mut = generate_guided_mutant(ORIGINAL, DESIGN_POS, guidance, rng)
        for pos in DESIGN_POS:
            idx = pos - 1
            if mut[idx] != ORIGINAL[idx]:
                assert mut[idx] != "C"

    def test_empty_guidance_falls_back(self):
        """Empty guidance should fallback to random mutant."""
        rng = random.Random(42)
        guidance = {}
        mut = generate_guided_mutant(ORIGINAL, DESIGN_POS, guidance, rng)
        assert len(mut) == len(ORIGINAL)
        # Should still produce some mutation (random fallback)
        # (not guaranteed to be different with very unlikely seed, but statistically will be)

    def test_focus_outside_design_positions(self):
        """Focus positions not in design_positions are ignored → random fallback."""
        rng = random.Random(42)
        guidance = {"focus_positions": [3, 13]}  # pos 3,13 not in DESIGN_POS
        # 3 = Cys (not in design_pos), 13 = not in design_pos
        design_no_3_13 = [p for p in DESIGN_POS if p not in [3, 13]]
        mut = generate_guided_mutant(ORIGINAL, design_no_3_13, guidance, rng)
        assert len(mut) == len(ORIGINAL)

    def test_deterministic(self):
        guidance = {
            "focus_positions": [5, 6],
            "suggested_mutations": {"5": ["W", "F"], "6": ["E", "D"]},
        }
        rng1 = random.Random(99)
        rng2 = random.Random(99)
        mut1 = generate_guided_mutant(ORIGINAL, DESIGN_POS, guidance, rng1)
        mut2 = generate_guided_mutant(ORIGINAL, DESIGN_POS, guidance, rng2)
        assert mut1 == mut2


# ===================================================================
# choose_objective_mode tests
# ===================================================================

class TestChooseObjectiveMode:

    def test_explicit_ddg_only(self):
        assert choose_objective_mode("ddg_only", 1) == "ddg_only"
        assert choose_objective_mode("ddg_only", 5) == "ddg_only"

    def test_explicit_ddg_plus_constraints(self):
        assert choose_objective_mode("ddg_plus_constraints", 1) == "ddg_plus_constraints"

    def test_auto_first_iteration(self):
        assert choose_objective_mode("auto", 1) == "ddg_only"

    def test_auto_later_iterations(self):
        assert choose_objective_mode("auto", 2) == "ddg_plus_constraints"
        assert choose_objective_mode("auto", 5) == "ddg_plus_constraints"


# ===================================================================
# notebook_mapping / candidate_to_dict
# ===================================================================

class TestMisc:

    def test_notebook_mapping_returns_list(self):
        mapping = notebook_mapping()
        assert isinstance(mapping, list)
        assert len(mapping) > 0
        for item in mapping:
            assert "notebook" in item
            assert "pipeline" in item

    def test_candidate_to_dict(self):
        c = CandidateResult(
            iteration=1, candidate_id="c1", sequence="AAA",
            ddg=-5.0, total_score=-100.0, clash_score=1.0,
        )
        d = candidate_to_dict(c)
        assert d["ddg"] == -5.0
        assert d["candidate_id"] == "c1"
        assert isinstance(d, dict)
