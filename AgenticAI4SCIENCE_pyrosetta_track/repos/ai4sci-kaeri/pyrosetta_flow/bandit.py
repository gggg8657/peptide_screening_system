"""
Multi-Armed Bandit Position Optimizer
======================================
Thompson Sampling bandit that learns which mutable positions are most
promising for producing favorable ddG values.  Each mutable position
maintains a Beta(alpha, beta) distribution; positions that historically
yield improvements get higher alpha, and positions that yield worsening
get higher beta.

Usage:
    bandit = PositionBandit()
    bandit.initialize_from_history(records)
    focus = bandit.sample_focus_positions(n=3)
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Dict, List

REFERENCE_SEQUENCE = "AGCKNFFWKTFTSC"
# Mutable positions (1-indexed, matching adapter.py convention)
MUTABLE_POSITIONS_1IDX = [1, 2, 4, 5, 6, 11, 12, 13]

DDG_PLAUSIBLE_MIN = -60.0
DDG_PLAUSIBLE_MAX = 200.0


class PositionBandit:
    """Thompson Sampling bandit over mutable peptide positions.

    Each position has a Beta(alpha, beta) prior.  Observing an improvement
    increments alpha; observing a worsening increments beta.
    """

    def __init__(
        self,
        positions: list[int] | None = None,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
    ) -> None:
        self.positions = positions or list(MUTABLE_POSITIONS_1IDX)
        self.arms: dict[int, dict[str, float]] = {
            pos: {"alpha": prior_alpha, "beta": prior_beta}
            for pos in self.positions
        }

    def initialize_from_history(self, records: list[dict]) -> None:
        """Bootstrap arm parameters from historical experiment records.

        For each candidate, identify which mutable positions were mutated
        relative to WT.  If the candidate's ddG is better (lower) than the
        WT mean, increment alpha for those positions; otherwise increment beta.
        """
        candidates = [
            r for r in records
            if r.get("record_type") == "candidate"
            and r.get("status") == "success"
            and DDG_PLAUSIBLE_MIN <= float(r.get("ddg", 999)) <= DDG_PLAUSIBLE_MAX
            and float(r.get("ddg", 999)) < 900
        ]
        if not candidates:
            return

        # Compute WT baseline mean ddG
        wt_ddgs: list[float] = []
        for r in candidates:
            seq = r.get("sequence", "")
            if seq == REFERENCE_SEQUENCE:
                wt_ddgs.append(float(r["ddg"]))

        # If no WT observations, use the median of all ddG values as baseline
        if wt_ddgs:
            baseline = sum(wt_ddgs) / len(wt_ddgs)
        else:
            all_ddgs = sorted(float(r["ddg"]) for r in candidates)
            baseline = all_ddgs[len(all_ddgs) // 2]

        for r in candidates:
            seq = r.get("sequence", "")
            if len(seq) != len(REFERENCE_SEQUENCE):
                continue
            ddg = float(r["ddg"])
            # Identify which mutable positions were changed
            mutated_positions = []
            for pos in self.positions:
                idx = pos - 1  # convert to 0-indexed
                if idx < len(seq) and seq[idx] != REFERENCE_SEQUENCE[idx]:
                    mutated_positions.append(pos)

            if not mutated_positions:
                continue

            improved = ddg < baseline
            for pos in mutated_positions:
                if improved:
                    self.arms[pos]["alpha"] += 1.0
                else:
                    self.arms[pos]["beta"] += 1.0

    def sample_focus_positions(self, n: int = 3, rng: random.Random | None = None) -> list[int]:
        """Thompson-sample from each arm's Beta distribution and return top-n positions."""
        if rng is None:
            rng = random.Random()

        samples: list[tuple[float, int]] = []
        for pos, params in self.arms.items():
            # Beta distribution sample via random.betavariate
            theta = rng.betavariate(params["alpha"], params["beta"])
            samples.append((theta, pos))

        # Return top-n positions with highest sampled values
        samples.sort(reverse=True)
        return [pos for _, pos in samples[:n]]

    def update(self, position: int, improved: bool) -> None:
        """Update a single arm after observing a result."""
        if position not in self.arms:
            return
        if improved:
            self.arms[position]["alpha"] += 1.0
        else:
            self.arms[position]["beta"] += 1.0

    def get_arm_stats(self) -> dict[int, dict[str, float]]:
        """Return current arm parameters and expected value for diagnostics."""
        stats = {}
        for pos, params in self.arms.items():
            a, b = params["alpha"], params["beta"]
            stats[pos] = {
                "alpha": a,
                "beta": b,
                "expected_value": round(a / (a + b), 4),
                "n_observations": int(a + b - 2),  # subtract priors
            }
        return stats
