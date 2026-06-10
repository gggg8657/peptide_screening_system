"""
Selective Mathematical Validation Module
==========================================
Validates user-selected top-k candidates for rank stability,
score decomposition consistency, and outlier/dominance detection.

Only operates on explicitly requested candidate sequences --
never validates all candidates automatically.

Data quality hardening (from devil's advocate findings):
- Plausibility filter: reject ddG < -60 or > 200 before any ranking
- Default top_k capped to 3 (not 5) due to high noise
- All results written to validation_status.json (NEVER STATUS_FILE)
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Plausibility bounds (shared with analysis.py)
# ---------------------------------------------------------------------------
DDG_PLAUSIBLE_MIN = -60.0
DDG_PLAUSIBLE_MAX = 200.0
DEFAULT_TOP_K = 3  # Capped to 3 due to high ddG noise across seeds


def _is_success(r: Dict[str, Any]) -> bool:
    return r.get("status") == "success" and float(r.get("ddg", 999)) < 900


def _is_plausible(r: Dict[str, Any]) -> bool:
    ddg = float(r.get("ddg", 999))
    return DDG_PLAUSIBLE_MIN <= ddg <= DDG_PLAUSIBLE_MAX


def _plausible_success(r: Dict[str, Any]) -> bool:
    return _is_success(r) and _is_plausible(r)


def _candidate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in records if r.get("record_type") == "candidate"]


# ---------------------------------------------------------------------------
# 3.1a  Rank Stability Validation
# ---------------------------------------------------------------------------

def validate_rank_stability(
    candidate_sequence: str,
    records: List[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
    min_appearances: int = 2,
) -> Dict[str, Any]:
    """Check if candidate's rank is stable across seeds/iterations.

    Uses plausibility-filtered data only.
    """
    all_cands = _candidate_records(records)

    # Build per-(run_id, iteration) rankings using plausible data only
    groups: Dict[tuple, List[Dict]] = defaultdict(list)
    for r in all_cands:
        if _plausible_success(r):
            groups[(r.get("run_id", ""), r.get("iteration", 0))].append(r)

    appearances = []
    for (rid, it), rows in sorted(groups.items()):
        ranked = sorted(rows, key=lambda x: float(x["ddg"]))
        for rank_idx, r in enumerate(ranked, start=1):
            if r.get("sequence") == candidate_sequence and rank_idx <= top_k:
                appearances.append({
                    "run_id": rid,
                    "iteration": it,
                    "rank": rank_idx,
                    "ddg": round(float(r["ddg"]), 4),
                    "n_candidates_in_group": len(ranked),
                })

    ranks = [a["rank"] for a in appearances]
    n = len(ranks)

    if n < min_appearances:
        return {
            "sequence": candidate_sequence,
            "stable": False,
            "confidence": 0.0,
            "detail": {
                "n_appearances": n,
                "ranks": ranks,
                "rank_stdev": 0.0,
                "rank_range": [min(ranks, default=0), max(ranks, default=0)],
                "consistency_score": 0.0,
                "threshold_used": float(top_k),
            },
            "verdict": f"Insufficient data: only {n} appearances (need >= {min_appearances})",
        }

    rank_stdev = statistics.stdev(ranks) if n > 1 else 0.0
    confidence = round(max(0.0, 1.0 - min(rank_stdev / top_k, 1.0)), 4)
    stable = confidence >= 0.7

    return {
        "sequence": candidate_sequence,
        "stable": stable,
        "confidence": confidence,
        "detail": {
            "n_appearances": n,
            "ranks": ranks,
            "rank_stdev": round(rank_stdev, 4),
            "rank_range": [min(ranks), max(ranks)],
            "consistency_score": confidence,
            "threshold_used": float(top_k),
            "appearances": appearances,
        },
        "verdict": (
            f"Stable: rank stdev={rank_stdev:.2f} across {n} appearances"
            if stable
            else f"Unstable: rank stdev={rank_stdev:.2f} across {n} appearances"
        ),
    }


# ---------------------------------------------------------------------------
# 3.1b  Score Decomposition Consistency
# ---------------------------------------------------------------------------

def validate_score_consistency(
    candidate_sequence: str,
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Check if ddG components are consistent across evaluations.

    Uses plausibility-filtered data to exclude scoring artifacts.
    """
    all_cands = _candidate_records(records)
    evals = [r for r in all_cands if r.get("sequence") == candidate_sequence and _plausible_success(r)]

    # Also count how many were filtered out
    all_evals = [r for r in all_cands if r.get("sequence") == candidate_sequence and _is_success(r)]
    n_filtered = len(all_evals) - len(evals)

    if len(evals) < 2:
        return {
            "sequence": candidate_sequence,
            "consistent": False,
            "confidence": 0.0,
            "detail": {
                "ddg_values": [round(float(e["ddg"]), 4) for e in evals],
                "ddg_mean": round(float(evals[0]["ddg"]), 4) if evals else 0.0,
                "ddg_stdev": 0.0,
                "ddg_cv": 0.0,
                "total_score_values": [],
                "total_score_stdev": 0.0,
                "clash_values": [],
                "ddg_total_ratio_stdev": 0.0,
                "anomalous_runs": [],
                "n_outliers_filtered": n_filtered,
            },
            "verdict": f"Insufficient plausible data: {len(evals)} evals ({n_filtered} filtered as outliers)",
        }

    ddg_vals = [float(e["ddg"]) for e in evals]
    ddg_mean = statistics.mean(ddg_vals)
    ddg_stdev = statistics.stdev(ddg_vals)
    ddg_cv = abs(ddg_stdev / ddg_mean) if abs(ddg_mean) > 1e-6 else 0.0

    total_vals = [float(e.get("total_score", 0)) for e in evals if e.get("total_score") is not None]
    total_stdev = statistics.stdev(total_vals) if len(total_vals) > 1 else 0.0

    clash_vals = [float(e.get("clash", 0)) for e in evals]

    # ddG-to-total_score ratio stability
    ratios = []
    for e in evals:
        ts = float(e.get("total_score", 0))
        if abs(ts) > 1e-6:
            ratios.append(float(e["ddg"]) / ts)
    ratio_stdev = statistics.stdev(ratios) if len(ratios) > 1 else 0.0

    # Detect anomalous runs (> 2 sigma from mean)
    anomalous = []
    if ddg_stdev > 1e-6:
        for e in evals:
            dev = abs(float(e["ddg"]) - ddg_mean) / ddg_stdev
            if dev > 2.0:
                anomalous.append({
                    "run_id": e.get("run_id", ""),
                    "iteration": e.get("iteration", 0),
                    "ddg": round(float(e["ddg"]), 4),
                    "deviation_sigma": round(dev, 2),
                })

    confidence = round(max(0.0, 1.0 - min(ddg_cv, 1.0)), 4)
    consistent = confidence >= 0.7

    return {
        "sequence": candidate_sequence,
        "consistent": consistent,
        "confidence": confidence,
        "detail": {
            "ddg_values": [round(d, 4) for d in ddg_vals],
            "ddg_mean": round(ddg_mean, 4),
            "ddg_stdev": round(ddg_stdev, 4),
            "ddg_cv": round(ddg_cv, 4),
            "ddg_range": round(max(ddg_vals) - min(ddg_vals), 4),
            "total_score_values": [round(t, 4) for t in total_vals],
            "total_score_stdev": round(total_stdev, 4),
            "clash_values": [round(c, 1) for c in clash_vals],
            "ddg_total_ratio_stdev": round(ratio_stdev, 6),
            "anomalous_runs": anomalous,
            "n_outliers_filtered": n_filtered,
        },
        "verdict": (
            f"Consistent: CV={ddg_cv:.3f}, stdev={ddg_stdev:.2f} across {len(evals)} evals"
            if consistent
            else f"Inconsistent: CV={ddg_cv:.3f}, stdev={ddg_stdev:.2f} across {len(evals)} evals"
        ),
    }


# ---------------------------------------------------------------------------
# 3.1c  Outlier / Dominance Detection
# ---------------------------------------------------------------------------

def validate_no_dominance(
    candidate_sequence: str,
    records: List[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
) -> Dict[str, Any]:
    """Check if candidate dominance is legitimate (not an artifact).

    Uses plausibility-filtered data to prevent scoring artifacts from
    creating false dominance signals.
    """
    all_cands = _candidate_records(records)
    real = [r for r in all_cands if _plausible_success(r)]

    # Aggregate MEDIAN ddG per unique sequence (more robust than best)
    seq_ddgs: Dict[str, List[float]] = defaultdict(list)
    seq_evals: Dict[str, int] = defaultdict(int)
    for r in real:
        seq = r.get("sequence", "")
        seq_ddgs[seq].append(float(r["ddg"]))
        seq_evals[seq] += 1

    seq_median: Dict[str, float] = {
        seq: statistics.median(ddgs) for seq, ddgs in seq_ddgs.items()
    }

    if candidate_sequence not in seq_median:
        return {
            "sequence": candidate_sequence,
            "dominance_detected": False,
            "legitimate": False,
            "confidence": 0.0,
            "detail": {},
            "verdict": "Candidate sequence not found in plausible records",
        }

    ranked = sorted(seq_median.items(), key=lambda x: x[1])
    cand_rank = next((i + 1 for i, (s, _) in enumerate(ranked) if s == candidate_sequence), len(ranked))
    cand_ddg = seq_median[candidate_sequence]

    # Top-k gaps
    top_ddgs = [ddg for _, ddg in ranked[:top_k]]
    gaps = [top_ddgs[i + 1] - top_ddgs[i] for i in range(len(top_ddgs) - 1)] if len(top_ddgs) > 1 else [0.0]
    mean_gap = statistics.mean([abs(g) for g in gaps]) if gaps else 0.0

    # Gap between this candidate and next-best
    next_best_ddg = ranked[1][1] if len(ranked) > 1 and cand_rank == 1 else (
        ranked[cand_rank][1] if cand_rank < len(ranked) else cand_ddg
    )
    ddg_gap = abs(next_best_ddg - cand_ddg)
    gap_ratio = ddg_gap / mean_gap if mean_gap > 1e-6 else 0.0
    is_gap_anomalous = gap_ratio > 2.0

    # Cluster analysis: candidates within 5 kcal/mol
    cluster_radius = 5.0
    cluster_size = sum(1 for _, d in ranked if abs(d - cand_ddg) <= cluster_radius)
    nearest_ddg = min(
        (abs(d - cand_ddg) for s, d in ranked if s != candidate_sequence),
        default=0.0,
    )

    # Reproducibility check: is this candidate consistently in top-k?
    groups: Dict[tuple, List[Dict]] = defaultdict(list)
    for r in real:
        groups[(r.get("run_id", ""), r.get("iteration", 0))].append(r)

    n_in_topk = 0
    n_groups_with_seq = 0
    for (rid, it), rows in groups.items():
        ranked_group = sorted(rows, key=lambda x: float(x["ddg"]))
        seq_in_group = [r for r in rows if r.get("sequence") == candidate_sequence]
        if seq_in_group:
            n_groups_with_seq += 1
            group_rank = next(
                (i + 1 for i, r in enumerate(ranked_group) if r.get("sequence") == candidate_sequence),
                len(ranked_group),
            )
            if group_rank <= top_k:
                n_in_topk += 1

    consistently_top = n_in_topk == n_groups_with_seq and n_groups_with_seq > 0

    dominance_detected = cand_rank == 1 and is_gap_anomalous
    legitimate = not is_gap_anomalous or (consistently_top and seq_evals.get(candidate_sequence, 0) >= 2)
    confidence = round(
        1.0 if not is_gap_anomalous else max(0.0, 1.0 - gap_ratio / 4.0),
        4,
    )

    return {
        "sequence": candidate_sequence,
        "dominance_detected": dominance_detected,
        "legitimate": legitimate,
        "confidence": confidence,
        "detail": {
            "candidate_rank": cand_rank,
            "candidate_median_ddg": round(cand_ddg, 4),
            "next_best_median_ddg": round(next_best_ddg, 4),
            "ddg_gap": round(ddg_gap, 4),
            "mean_gap_in_top_k": round(mean_gap, 4),
            "gap_ratio": round(gap_ratio, 4),
            "is_gap_anomalous": is_gap_anomalous,
            "n_evaluations": seq_evals.get(candidate_sequence, 0),
            "consistently_top": consistently_top,
            "ranking_metric": "median_ddg",
            "cluster_analysis": {
                "nearest_neighbor_distance": round(nearest_ddg, 4),
                "cluster_size": cluster_size,
                "cluster_radius_kcal": cluster_radius,
            },
        },
        "verdict": (
            f"Rank #{cand_rank} (median ddG), gap_ratio={gap_ratio:.2f}: "
            + ("Anomalous dominance" if dominance_detected and not legitimate else
               "Dominant but reproducible" if dominance_detected else
               "No anomalous dominance")
        ),
    }


# ---------------------------------------------------------------------------
# 3.1d  Combined Validation
# ---------------------------------------------------------------------------

_WEIGHTS = {"rank_stability": 0.4, "score_consistency": 0.4, "dominance": 0.2}


def validate_candidate(
    candidate_sequence: str,
    records: List[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
) -> Dict[str, Any]:
    """Run all three validations and produce combined report."""
    rank_result = validate_rank_stability(candidate_sequence, records, top_k=top_k)
    score_result = validate_score_consistency(candidate_sequence, records)
    dom_result = validate_no_dominance(candidate_sequence, records, top_k=top_k)

    overall = round(
        _WEIGHTS["rank_stability"] * rank_result["confidence"]
        + _WEIGHTS["score_consistency"] * score_result["confidence"]
        + _WEIGHTS["dominance"] * dom_result["confidence"],
        4,
    )

    if overall >= 0.7:
        verdict = "RELIABLE"
    elif overall >= 0.4:
        verdict = "CAUTION"
    else:
        verdict = "UNRELIABLE"

    return {
        "sequence": candidate_sequence,
        "overall_confidence": overall,
        "overall_verdict": verdict,
        "validations": {
            "rank_stability": rank_result,
            "score_consistency": score_result,
            "dominance_check": dom_result,
        },
        "plausibility_filter": {
            "ddg_min": DDG_PLAUSIBLE_MIN,
            "ddg_max": DDG_PLAUSIBLE_MAX,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def validate_batch(
    candidate_sequences: List[str],
    records: List[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
) -> Dict[str, Any]:
    """Validate multiple user-selected candidates.

    top_k defaults to 3 (capped due to high ddG noise).
    """
    results = [validate_candidate(seq, records, top_k=top_k) for seq in candidate_sequences]

    n_reliable = sum(1 for r in results if r["overall_verdict"] == "RELIABLE")
    n_caution = sum(1 for r in results if r["overall_verdict"] == "CAUTION")
    n_unreliable = sum(1 for r in results if r["overall_verdict"] == "UNRELIABLE")

    return {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "n_candidates": len(results),
        "top_k_used": top_k,
        "plausibility_filter": {
            "ddg_min": DDG_PLAUSIBLE_MIN,
            "ddg_max": DDG_PLAUSIBLE_MAX,
        },
        "results": results,
        "summary": {
            "n_reliable": n_reliable,
            "n_caution": n_caution,
            "n_unreliable": n_unreliable,
        },
    }
