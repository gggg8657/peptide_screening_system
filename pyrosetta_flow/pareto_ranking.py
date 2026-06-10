"""NSGA-II Pareto Ranking for radiopharmaceutical candidate selection.

Replaces the legacy weighted-sum scoring (0.45/0.20/0.15/0.10/0.10) with
pymoo-based Non-dominated Sorting + Crowding Distance.

Objectives (all minimized):
    1. ddG              (lower is better binding)
    2. -stability        (negate so lower = more stable)
    3. -druggability     (negate so lower = more drug-like)
    4. -diversity        (negate so lower = more diverse)

Constraints:
    - hard_violations <= 0
    - clash_score <= threshold (default 10.0)
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.operators.survival.rank_and_crowding.metrics import calc_crowding_distance


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_OBJECTIVE_KEYS = ("ddG", "stability", "druggability", "diversity")
_CONSTRAINT_KEYS = ("hard_violations", "clash_score")
_DEFAULT_CLASH_THRESHOLD = 10.0


def _extract_objectives(candidate: Dict) -> List[float]:
    """Return a list of objective values ready for minimisation.

    Parameters
    ----------
    candidate : dict
        Must contain keys ``ddG``, ``stability``, ``druggability``,
        ``diversity``.  Missing values are treated as ``0.0``.

    Returns
    -------
    list[float]
        ``[ddG, -stability, -druggability, -diversity]``
    """
    ddg = float(candidate.get("ddG", 0.0))
    stab = float(candidate.get("stability", 0.0))
    drug = float(candidate.get("druggability", 0.0))
    div = float(candidate.get("diversity", 0.0))
    return [ddg, -stab, -drug, -div]


def _extract_constraints(
    candidate: Dict,
    clash_threshold: float = _DEFAULT_CLASH_THRESHOLD,
) -> List[float]:
    """Return constraint violation values (<=0 means feasible).

    Parameters
    ----------
    candidate : dict
        Expected keys: ``hard_violations``, ``clash_score``.
    clash_threshold : float
        Maximum allowed clash score.

    Returns
    -------
    list[float]
        ``[hard_violations, clash_score - threshold]``
        Both must be ``<= 0`` for the candidate to be feasible.
    """
    hv = float(candidate.get("hard_violations", 0))
    cs = float(candidate.get("clash_score", 0.0))
    return [hv, cs - clash_threshold]


def _penalise_infeasible(
    fronts: List[List[int]],
    cv: np.ndarray,
) -> List[List[int]]:
    """Push infeasible solutions behind all feasible fronts.

    Any candidate with ``cv > 0`` is removed from its current front and
    appended to a single penalty front at the end, sorted by total
    constraint violation (ascending).

    Parameters
    ----------
    fronts : list[list[int]]
        Non-dominated fronts (indices).
    cv : ndarray of shape (n,)
        Overall constraint violation per candidate.

    Returns
    -------
    list[list[int]]
        Adjusted fronts with infeasible candidates relegated.
    """
    feasible_fronts: List[List[int]] = []
    infeasible_indices: List[int] = []

    for front in fronts:
        feas = [i for i in front if cv[i] <= 0.0]
        infeas = [i for i in front if cv[i] > 0.0]
        if feas:
            feasible_fronts.append(feas)
        infeasible_indices.extend(infeas)

    if infeasible_indices:
        # Sort by total constraint violation (lower first — less bad)
        infeasible_indices.sort(key=lambda i: cv[i])
        feasible_fronts.append(infeasible_indices)

    return feasible_fronts


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def pareto_rank_candidates(
    candidates: List[Dict],
    clash_threshold: float = _DEFAULT_CLASH_THRESHOLD,
) -> List[Dict]:
    """Assign ``pareto_rank`` and ``crowding_distance`` to each candidate.

    Uses pymoo's *NonDominatedSorting* (NSGA-II fast non-dominated sort)
    followed by crowding-distance calculation within each front.
    Infeasible candidates (``hard_violations > 0`` or ``clash_score >
    clash_threshold``) are automatically pushed behind all feasible fronts.

    Parameters
    ----------
    candidates : list[dict]
        Each dict must contain at least ``ddG``, ``stability``,
        ``druggability``, ``diversity``.  ``hard_violations`` and
        ``clash_score`` are optional (default 0).
    clash_threshold : float, optional
        Maximum allowed clash score (default 10.0).

    Returns
    -------
    list[dict]
        The *same* dicts, mutated in-place with two new keys:

        - ``pareto_rank`` (int): 0 = first Pareto front (best).
        - ``crowding_distance`` (float): higher is more isolated / diverse.
    """
    n = len(candidates)
    if n == 0:
        return candidates

    # Build objective matrix (n x 4) — all minimised
    F = np.array([_extract_objectives(c) for c in candidates], dtype=float)

    # Build constraint-violation vector
    G = np.array(
        [_extract_constraints(c, clash_threshold) for c in candidates],
        dtype=float,
    )
    # Overall CV = sum of positive violations
    cv = np.sum(np.maximum(G, 0.0), axis=1)

    # Non-dominated sorting on objectives only
    nds = NonDominatedSorting()
    fronts = list(nds.do(F))

    # Push infeasible behind feasible
    fronts = _penalise_infeasible(fronts, cv)

    # Assign rank + crowding distance
    for rank, front in enumerate(fronts):
        front_arr = np.array(front)
        F_front = F[front_arr]

        if len(front_arr) <= 2:
            # pymoo crowding distance sets boundary points to inf
            cd = np.full(len(front_arr), math.inf)
        else:
            cd = calc_crowding_distance(F_front)

        for local_idx, global_idx in enumerate(front):
            candidates[global_idx]["pareto_rank"] = rank
            candidates[global_idx]["crowding_distance"] = float(cd[local_idx])

    return candidates


def select_from_pareto_front(
    ranked: List[Dict],
    n: int,
    prefer_feasible: bool = True,
) -> List[Dict]:
    """Select the top *n* candidates from Pareto-ranked results.

    Selection priority:
    1. Lower ``pareto_rank`` (front 0 first).
    2. Higher ``crowding_distance`` as tiebreaker within the same front.

    Parameters
    ----------
    ranked : list[dict]
        Candidates already processed by :func:`pareto_rank_candidates`.
    n : int
        Number of candidates to return.
    prefer_feasible : bool, optional
        If ``True`` (default), feasible candidates (``hard_violations <= 0``)
        are selected before infeasible ones regardless of rank.  This is
        already handled by :func:`pareto_rank_candidates`, but the flag
        provides an explicit guarantee.

    Returns
    -------
    list[dict]
        Up to *n* candidates, sorted by rank then crowding distance.
    """
    if n <= 0:
        return []

    def _sort_key(c: Dict) -> tuple:
        rank = c.get("pareto_rank", 999)
        cd = c.get("crowding_distance", 0.0)
        # Negate cd so higher crowding distance sorts first
        return (rank, -cd)

    selected = sorted(ranked, key=_sort_key)
    return selected[:n]
