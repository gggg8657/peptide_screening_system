"""
Analysis Pipeline for Paper Evidence
======================================
Pure-function module that computes convergence trends, rank stability,
gate pass/fail distribution, and candidate selection evidence from
experiment_log.jsonl records.

All functions operate on pre-loaded records (List[Dict]) and return
plain dicts suitable for JSON serialization.

Data quality notes (from devil's advocate analysis):
- ddG stdev across dataset = ~71 kcal/mol (enormous noise)
- Same sequence can produce ddG range of 535 across seeds
- 6.6% of values are extreme outliers (ddG < -60 or > 200)
- Plausibility filter applied: reject ddG < -60 or > 200 as scoring artifacts
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Plausibility bounds -- values outside are scoring artifacts
# ---------------------------------------------------------------------------
DDG_PLAUSIBLE_MIN = -60.0   # kcal/mol; below this is likely artifact
DDG_PLAUSIBLE_MAX = 200.0   # kcal/mol; above this is likely artifact


def load_and_filter(
    records: List[Dict[str, Any]],
    run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter records to candidate type, optionally by run_id."""
    out = [r for r in records if r.get("record_type") == "candidate"]
    if run_id:
        out = [r for r in out if r.get("run_id") == run_id]
    return out


def _is_success(r: Dict[str, Any]) -> bool:
    return r.get("status") == "success" and float(r.get("ddg", 999)) < 900


def _is_plausible(r: Dict[str, Any]) -> bool:
    """Check if a successful record has a plausible ddG value."""
    ddg = float(r.get("ddg", 999))
    return DDG_PLAUSIBLE_MIN <= ddg <= DDG_PLAUSIBLE_MAX


def _plausible_success(r: Dict[str, Any]) -> bool:
    """Success AND within plausible ddG range."""
    return _is_success(r) and _is_plausible(r)


def _group_key(r: Dict[str, Any]) -> tuple:
    return (r.get("run_id", ""), r.get("iteration", 0))


# ---------------------------------------------------------------------------
# 2.1a  Convergence Trends (with cross-run variance and outlier flagging)
# ---------------------------------------------------------------------------

def convergence_by_iteration(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Per-(run_id, iteration) convergence statistics with outlier flagging."""
    candidates = load_and_filter(records)
    groups: Dict[tuple, List[Dict]] = defaultdict(list)
    for r in candidates:
        groups[_group_key(r)].append(r)

    result: List[Dict[str, Any]] = []
    for (rid, it), rows in sorted(groups.items()):
        successes = [r for r in rows if _is_success(r)]
        plausible = [r for r in rows if _plausible_success(r)]
        outliers = [r for r in successes if not _is_plausible(r)]

        ddgs_raw = [float(r["ddg"]) for r in successes]
        ddgs = [float(r["ddg"]) for r in plausible]
        n_total = len(rows)
        n_success = len(successes)

        entry: Dict[str, Any] = {
            "run_id": rid,
            "iteration": it,
            "best_ddg": round(min(ddgs), 4) if ddgs else None,
            "mean_ddg": round(statistics.mean(ddgs), 4) if ddgs else None,
            "median_ddg": round(statistics.median(ddgs), 4) if ddgs else None,
            "max_ddg": round(max(ddgs), 4) if ddgs else None,
            "ddg_stdev": round(statistics.stdev(ddgs), 4) if len(ddgs) > 1 else 0.0,
            "n_total": n_total,
            "n_success": n_success,
            "n_plausible": len(plausible),
            "n_failed": n_total - n_success,
            "n_outliers_flagged": len(outliers),
            "n_selected": sum(1 for r in rows if r.get("selected")),
            "success_rate": round(n_success / n_total, 4) if n_total else 0.0,
        }
        if outliers:
            entry["outlier_ddgs"] = [round(float(r["ddg"]), 4) for r in outliers]
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Cross-run variance per sequence
# ---------------------------------------------------------------------------

def cross_run_variance(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Per-sequence ddG variance across different runs/iterations.

    Highlights the enormous noise problem: same sequence can produce
    very different ddG values across seeds.
    """
    candidates = load_and_filter(records)
    seq_data: Dict[str, List[Dict]] = defaultdict(list)
    for r in candidates:
        if _plausible_success(r):
            seq_data[r.get("sequence", "")].append(r)

    results = []
    for seq, evals in seq_data.items():
        if len(evals) < 2:
            continue
        ddgs = [float(e["ddg"]) for e in evals]
        results.append({
            "sequence": seq,
            "n_observations": len(evals),
            "runs_seen": sorted(set(e.get("run_id", "") for e in evals)),
            "ddg_min": round(min(ddgs), 4),
            "ddg_max": round(max(ddgs), 4),
            "ddg_range": round(max(ddgs) - min(ddgs), 4),
            "ddg_mean": round(statistics.mean(ddgs), 4),
            "ddg_median": round(statistics.median(ddgs), 4),
            "ddg_stdev": round(statistics.stdev(ddgs), 4),
        })
    results.sort(key=lambda x: x["ddg_range"], reverse=True)

    return {
        "n_sequences_with_multiple_obs": len(results),
        "sequences": results,
    }


# ---------------------------------------------------------------------------
# 2.1b  Rank Stability (with top-5 overlap metric)
# ---------------------------------------------------------------------------

def rank_stability(
    records: List[Dict[str, Any]],
    top_k: int = 10,
) -> Dict[str, Any]:
    """Track how top-k sequences' ranks shift across iterations/runs.

    Includes top-5 overlap between consecutive iterations per run.
    """
    candidates = load_and_filter(records)
    groups: Dict[tuple, List[Dict]] = defaultdict(list)
    for r in candidates:
        if _plausible_success(r):
            groups[_group_key(r)].append(r)

    # Build per-iteration rankings
    seq_appearances: Dict[str, List[Dict]] = defaultdict(list)
    iteration_top5: Dict[str, Dict[int, set]] = defaultdict(lambda: defaultdict(set))

    for (rid, it), rows in sorted(groups.items()):
        ranked = sorted(rows, key=lambda x: float(x["ddg"]))
        for rank_idx, r in enumerate(ranked[:top_k], start=1):
            seq = r.get("sequence", "")
            seq_appearances[seq].append({
                "run_id": rid,
                "iteration": it,
                "rank": rank_idx,
                "ddg": round(float(r["ddg"]), 4),
            })
            if rank_idx <= 5:
                iteration_top5[rid][it].add(seq)

    sequences = []
    for seq, apps in seq_appearances.items():
        ranks = [a["rank"] for a in apps]
        volatility = round(statistics.stdev(ranks), 4) if len(ranks) > 1 else 0.0
        sequences.append({
            "sequence": seq,
            "appearances": apps,
            "n_appearances": len(apps),
            "rank_volatility": volatility,
            "best_rank": min(ranks),
            "worst_rank": max(ranks),
            "mean_rank": round(statistics.mean(ranks), 2),
        })
    sequences.sort(key=lambda s: s["mean_rank"])

    # Compute top-5 overlap between consecutive iterations per run
    top5_overlaps = []
    for rid, iter_sets in sorted(iteration_top5.items()):
        iters = sorted(iter_sets.keys())
        for i in range(len(iters) - 1):
            it_a, it_b = iters[i], iters[i + 1]
            set_a, set_b = iter_sets[it_a], iter_sets[it_b]
            overlap = len(set_a & set_b)
            top5_overlaps.append({
                "run_id": rid,
                "iteration_a": it_a,
                "iteration_b": it_b,
                "overlap_count": overlap,
                "overlap_ratio": round(overlap / 5, 4) if set_a and set_b else 0.0,
                "shared_sequences": sorted(set_a & set_b),
            })

    return {
        "top_k": top_k,
        "n_unique_sequences": len(sequences),
        "sequences": sequences,
        "top5_overlap_between_iterations": top5_overlaps,
        "plausibility_filter": {
            "ddg_min": DDG_PLAUSIBLE_MIN,
            "ddg_max": DDG_PLAUSIBLE_MAX,
        },
    }


# ---------------------------------------------------------------------------
# 2.1c  Gate Pass/Fail Distribution
# ---------------------------------------------------------------------------

def gate_distribution(
    records: List[Dict[str, Any]],
    ddg_threshold: float = -5.0,
    clash_threshold: float = 10.0,
) -> Dict[str, Any]:
    """QC gate pass/fail counts broken down by gate, run, iteration, and failure mode."""
    candidates = load_and_filter(records)
    n_total = len(candidates)
    n_success = sum(1 for r in candidates if r.get("status") == "success")
    n_failed = n_total - n_success

    # Gate-level counts (only among non-sentinel successes)
    real = [r for r in candidates if _is_success(r)]
    plausible = [r for r in candidates if _plausible_success(r)]
    outlier_count = len(real) - len(plausible)

    ddg_passed = sum(1 for r in plausible if float(r["ddg"]) <= ddg_threshold)
    clash_passed = sum(1 for r in plausible if float(r.get("clash", 999)) <= clash_threshold)
    combined_passed = sum(
        1 for r in plausible
        if float(r["ddg"]) <= ddg_threshold and float(r.get("clash", 999)) <= clash_threshold
    )

    # Positive (unfavorable) ddG count
    positive_ddg = sum(1 for r in real if float(r["ddg"]) > 0)

    # By run
    by_run: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0, "ddg_passed": 0, "outliers": 0})
    for r in candidates:
        rid = r.get("run_id", "unknown")
        by_run[rid]["total"] += 1
        if _is_success(r):
            by_run[rid]["success"] += 1
            if not _is_plausible(r):
                by_run[rid]["outliers"] += 1
            elif float(r["ddg"]) <= ddg_threshold:
                by_run[rid]["ddg_passed"] += 1
        else:
            by_run[rid]["failed"] += 1

    # By iteration
    groups: Dict[tuple, List[Dict]] = defaultdict(list)
    for r in candidates:
        groups[_group_key(r)].append(r)

    by_iteration = []
    for (rid, it), rows in sorted(groups.items()):
        s = [r for r in rows if _plausible_success(r)]
        p = sum(1 for r in s if float(r["ddg"]) <= ddg_threshold)
        by_iteration.append({
            "run_id": rid,
            "iteration": it,
            "total": len(rows),
            "passed": p,
            "failed": len(rows) - len([r for r in rows if _is_success(r)]),
            "outliers_flagged": len([r for r in rows if _is_success(r) and not _is_plausible(r)]),
            "pass_rate": round(p / len(rows), 4) if rows else 0.0,
        })

    # Failure modes
    segfault = sum(1 for r in candidates if "egmentation fault" in r.get("error_summary", ""))
    sentinel_fail = sum(1 for r in candidates if r.get("status") == "failed")
    high_ddg = sum(1 for r in plausible if float(r["ddg"]) > ddg_threshold)
    high_clash = sum(1 for r in plausible if float(r.get("clash", 999)) > clash_threshold)
    both = sum(
        1 for r in plausible
        if float(r["ddg"]) > ddg_threshold and float(r.get("clash", 999)) > clash_threshold
    )
    extreme_ddg = sum(
        1 for r in real
        if float(r["ddg"]) < DDG_PLAUSIBLE_MIN or float(r["ddg"]) > DDG_PLAUSIBLE_MAX
    )

    return {
        "total_candidates": n_total,
        "by_status": {"success": n_success, "failed": n_failed},
        "data_quality": {
            "n_plausible": len(plausible),
            "n_outliers_removed": outlier_count,
            "n_positive_ddg": positive_ddg,
            "n_extreme_ddg": extreme_ddg,
            "plausibility_bounds": {"min": DDG_PLAUSIBLE_MIN, "max": DDG_PLAUSIBLE_MAX},
        },
        "by_gate": {
            "ddg_gate": {"passed": ddg_passed, "failed": len(plausible) - ddg_passed, "threshold": ddg_threshold},
            "clash_gate": {"passed": clash_passed, "failed": len(plausible) - clash_passed, "threshold": clash_threshold},
            "combined_gate": {"passed": combined_passed, "failed": len(plausible) - combined_passed},
        },
        "by_run": dict(by_run),
        "by_iteration": by_iteration,
        "failure_modes": {
            "rosetta_segfault": segfault,
            "script_failure_total": sentinel_fail,
            "high_ddg": high_ddg,
            "high_clash": high_clash,
            "both_ddg_and_clash": both,
            "extreme_ddg_artifacts": extreme_ddg,
        },
    }


# ---------------------------------------------------------------------------
# 2.1d  Candidate Selection Evidence (with reproducibility metrics)
# ---------------------------------------------------------------------------

def candidate_evidence(
    records: List[Dict[str, Any]],
    top_k: int = 10,
    ddg_threshold: float = -5.0,
    clash_threshold: float = 10.0,
) -> Dict[str, Any]:
    """Paper-ready evidence summary for top candidates across all runs.

    Uses plausibility-filtered data and includes min/median/max reproducibility.
    """
    candidates = load_and_filter(records)
    real = [r for r in candidates if _plausible_success(r)]

    # Aggregate by sequence
    seq_data: Dict[str, List[Dict]] = defaultdict(list)
    for r in real:
        seq_data[r.get("sequence", "")].append(r)

    # Rank by MEDIAN ddG across all evaluations (more robust than best)
    seq_summaries = []
    for seq, evals in seq_data.items():
        ddgs = [float(e["ddg"]) for e in evals]
        clashes = [float(e.get("clash", 0)) for e in evals]
        n_selected = sum(1 for e in evals if e.get("selected"))
        seq_summaries.append({
            "sequence": seq,
            "best_ddg": round(min(ddgs), 4),
            "median_ddg": round(statistics.median(ddgs), 4),
            "mean_ddg": round(statistics.mean(ddgs), 4),
            "max_ddg": round(max(ddgs), 4),
            "ddg_range": round(max(ddgs) - min(ddgs), 4),
            "ddg_stdev": round(statistics.stdev(ddgs), 4) if len(ddgs) > 1 else 0.0,
            "n_evaluations": len(evals),
            "n_selected": n_selected,
            "consistency": round(n_selected / len(evals), 4) if evals else 0.0,
            "runs_seen": sorted(set(e.get("run_id", "") for e in evals)),
            "ddg_values": [round(d, 4) for d in ddgs],
            "clash_values": [round(c, 1) for c in clashes],
            "clash_mean": round(statistics.mean(clashes), 2) if clashes else 0.0,
        })

    # Sort by median ddG (more robust than best given high noise)
    seq_summaries.sort(key=lambda s: s["median_ddg"])
    top = seq_summaries[:top_k]
    for rank_idx, s in enumerate(top, start=1):
        s["rank"] = rank_idx

    return {
        "top_candidates": top,
        "total_unique_sequences": len(seq_summaries),
        "selection_criteria": {
            "ddg_threshold": ddg_threshold,
            "clash_threshold": clash_threshold,
            "top_k": top_k,
            "ranking_metric": "median_ddg",
            "plausibility_filter": {"min": DDG_PLAUSIBLE_MIN, "max": DDG_PLAUSIBLE_MAX},
        },
    }


# ---------------------------------------------------------------------------
# Combined summary
# ---------------------------------------------------------------------------

def compute_full_analysis(
    records: List[Dict[str, Any]],
    ddg_threshold: float = -5.0,
    clash_threshold: float = 10.0,
    top_k: int = 10,
) -> Dict[str, Any]:
    """Run all analyses and return combined result."""
    return {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "plausibility_filter": {"ddg_min": DDG_PLAUSIBLE_MIN, "ddg_max": DDG_PLAUSIBLE_MAX},
        "convergence": convergence_by_iteration(records),
        "cross_run_variance": cross_run_variance(records),
        "rank_stability": rank_stability(records, top_k=top_k),
        "gate_distribution": gate_distribution(records, ddg_threshold, clash_threshold),
        "candidate_evidence": candidate_evidence(records, top_k, ddg_threshold, clash_threshold),
    }
