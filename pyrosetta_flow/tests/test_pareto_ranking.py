"""Tests for NSGA-II Pareto ranking module."""
from __future__ import annotations

import math
from typing import Dict, List

import pytest

from pyrosetta_flow.pareto_ranking import (
    pareto_rank_candidates,
    select_from_pareto_front,
)


# ---------------------------------------------------------------------------
# Fixtures — 5 mock candidates
# ---------------------------------------------------------------------------

def _make_candidates() -> List[Dict]:
    """Create 5 mock candidates with known dominance relationships.

    Candidate layout (all objectives minimised after sign-flip):
        A: best ddG, good stability        -> expected front 0
        B: best stability, good ddG         -> expected front 0
        C: moderate on all axes             -> expected front 1
        D: good objectives but INFEASIBLE   -> pushed behind all feasible
        E: worst on everything              -> expected dominated
    """
    return [
        {
            "name": "A",
            "ddG": -30.0,
            "stability": 0.9,
            "druggability": 0.7,
            "diversity": 0.5,
            "hard_violations": 0,
            "clash_score": 2.0,
        },
        {
            "name": "B",
            "ddG": -20.0,
            "stability": 0.95,
            "druggability": 0.8,
            "diversity": 0.6,
            "hard_violations": 0,
            "clash_score": 1.0,
        },
        {
            "name": "C",
            "ddG": -15.0,
            "stability": 0.6,
            "druggability": 0.5,
            "diversity": 0.4,
            "hard_violations": 0,
            "clash_score": 3.0,
        },
        {
            "name": "D",
            "ddG": -35.0,
            "stability": 0.99,
            "druggability": 0.9,
            "diversity": 0.8,
            "hard_violations": 2,  # INFEASIBLE
            "clash_score": 1.0,
        },
        {
            "name": "E",
            "ddG": -5.0,
            "stability": 0.3,
            "druggability": 0.2,
            "diversity": 0.1,
            "hard_violations": 0,
            "clash_score": 5.0,
        },
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParetoRankCandidates:
    """Tests for pareto_rank_candidates."""

    def test_all_candidates_receive_rank_and_cd(self) -> None:
        candidates = _make_candidates()
        result = pareto_rank_candidates(candidates)

        assert len(result) == 5
        for c in result:
            assert "pareto_rank" in c
            assert "crowding_distance" in c
            assert isinstance(c["pareto_rank"], int)
            assert isinstance(c["crowding_distance"], float)

    def test_front0_not_dominated_by_any_feasible(self) -> None:
        """Candidates on front 0 must not be dominated by other feasible
        candidates on front 0."""
        candidates = _make_candidates()
        result = pareto_rank_candidates(candidates)

        front0 = [c for c in result if c["pareto_rank"] == 0]
        assert len(front0) >= 1, "front 0 should contain at least one candidate"

        # Verify no front-0 candidate dominates another front-0 candidate
        # (non-domination check)
        objs = []
        for c in front0:
            objs.append([
                c["ddG"],
                -c["stability"],
                -c["druggability"],
                -c["diversity"],
            ])

        for i, oi in enumerate(objs):
            for j, oj in enumerate(objs):
                if i == j:
                    continue
                # oi dominates oj if oi <= oj on all and < on at least one
                all_leq = all(a <= b for a, b in zip(oi, oj))
                any_lt = any(a < b for a, b in zip(oi, oj))
                assert not (all_leq and any_lt), (
                    f"front-0 candidate {front0[i]['name']} dominates "
                    f"{front0[j]['name']} — should be impossible on same front"
                )

    def test_infeasible_pushed_behind_feasible(self) -> None:
        """Candidate D has hard_violations=2 and must rank worse than
        all feasible candidates."""
        candidates = _make_candidates()
        result = pareto_rank_candidates(candidates)

        cand_d = next(c for c in result if c["name"] == "D")
        feasible = [c for c in result if c.get("hard_violations", 0) <= 0]

        max_feasible_rank = max(c["pareto_rank"] for c in feasible)
        assert cand_d["pareto_rank"] > max_feasible_rank, (
            f"Infeasible D (rank {cand_d['pareto_rank']}) should be behind "
            f"all feasible candidates (max rank {max_feasible_rank})"
        )

    def test_clash_score_violation(self) -> None:
        """A candidate exceeding clash threshold is treated as infeasible."""
        candidates = [
            {
                "name": "OK",
                "ddG": -10.0,
                "stability": 0.5,
                "druggability": 0.5,
                "diversity": 0.5,
                "hard_violations": 0,
                "clash_score": 5.0,
            },
            {
                "name": "CLASH",
                "ddG": -20.0,
                "stability": 0.9,
                "druggability": 0.9,
                "diversity": 0.9,
                "hard_violations": 0,
                "clash_score": 15.0,  # > default threshold 10
            },
        ]
        result = pareto_rank_candidates(candidates)

        ok = next(c for c in result if c["name"] == "OK")
        clash = next(c for c in result if c["name"] == "CLASH")
        assert clash["pareto_rank"] > ok["pareto_rank"]

    def test_empty_input(self) -> None:
        assert pareto_rank_candidates([]) == []


class TestSelectFromParetoFront:
    """Tests for select_from_pareto_front."""

    def test_select_top_2(self) -> None:
        candidates = _make_candidates()
        ranked = pareto_rank_candidates(candidates)
        top2 = select_from_pareto_front(ranked, 2)

        assert len(top2) == 2
        assert all(c["pareto_rank"] == 0 for c in top2), (
            "Top-2 should come from front 0"
        )

    def test_select_more_than_available(self) -> None:
        candidates = _make_candidates()
        ranked = pareto_rank_candidates(candidates)
        selected = select_from_pareto_front(ranked, 100)
        assert len(selected) == len(candidates)

    def test_select_zero(self) -> None:
        candidates = _make_candidates()
        ranked = pareto_rank_candidates(candidates)
        assert select_from_pareto_front(ranked, 0) == []

    def test_ordering_by_rank_then_crowding(self) -> None:
        """Selected candidates must be sorted: lower rank first,
        then higher crowding distance first."""
        candidates = _make_candidates()
        ranked = pareto_rank_candidates(candidates)
        selected = select_from_pareto_front(ranked, len(candidates))

        for i in range(len(selected) - 1):
            a, b = selected[i], selected[i + 1]
            if a["pareto_rank"] == b["pareto_rank"]:
                assert a["crowding_distance"] >= b["crowding_distance"]
            else:
                assert a["pareto_rank"] < b["pareto_rank"]
