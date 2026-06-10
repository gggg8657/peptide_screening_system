"""Cross-experiment aggregation — load results from output dirs and compute summary tables."""
from __future__ import annotations

import json
import logging
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"


def load_phase_results(phase: str) -> List[Dict[str, Any]]:
    """Load all completed experiment results from a phase directory."""
    phase_dir = OUTPUTS_DIR / phase
    if not phase_dir.exists():
        logger.warning("Phase dir not found: %s", phase_dir)
        return []

    results = []
    for run_dir in sorted(phase_dir.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("_"):
            continue

        status_file = run_dir / "status.json"
        ses_file = run_dir / "ses_score.json"
        config_file = run_dir / "config_snapshot.json"

        if not status_file.exists():
            continue

        try:
            status = json.loads(status_file.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping %s: bad status.json: %s", run_dir.name, exc)
            continue
        if status.get("state") != "done":
            continue

        # Parse run dir name: {model}__{flow}__{gate_mode}__s{seed}
        parts = run_dir.name.split("__")
        model = parts[0] if len(parts) >= 1 else "unknown"
        flow = parts[1] if len(parts) >= 2 else "sequential"
        # Find seed (last part starting with 's') and gate_mode
        seed_str = "0"
        gate_mode = "static"
        for p in parts[2:]:
            if p.startswith("s") and p[1:].isdigit():
                seed_str = p.lstrip("s")
            elif p in ("static", "adaptive"):
                gate_mode = p

        entry: Dict[str, Any] = {
            "run_dir": str(run_dir),
            "model": model,
            "flow": flow,
            "gate_mode": gate_mode,
            "seed": int(seed_str),
            "elapsed_s": status.get("elapsed_s", 0),
        }

        if ses_file.exists():
            try:
                entry["ses"] = json.loads(ses_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        if config_file.exists():
            try:
                entry["config"] = json.loads(config_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        results.append(entry)

    return results


def aggregate_by_model(results: List[Dict]) -> Dict[str, Dict]:
    """Group results by model and compute mean/stdev SES."""
    groups: Dict[str, List[Dict]] = {}
    for r in results:
        groups.setdefault(r["model"], []).append(r)

    summary = {}
    for model, runs in sorted(groups.items()):
        ses_values = [r["ses"]["ses"] for r in runs if "ses" in r]
        ddg_values = [r["ses"]["best_ddg"] for r in runs if "ses" in r]

        summary[model] = {
            "n_runs": len(runs),
            "n_done": len(ses_values),
            "ses_mean": round(statistics.mean(ses_values), 4) if ses_values else None,
            "ses_stdev": round(statistics.stdev(ses_values), 4) if len(ses_values) >= 2 else None,
            "best_ddg_mean": round(statistics.mean(ddg_values), 3) if ddg_values else None,
            "mean_elapsed_s": round(statistics.mean(r["elapsed_s"] for r in runs), 1),
        }

    return summary


def aggregate_by_model_flow(results: List[Dict]) -> Dict[str, Dict]:
    """Group results by (model, flow) and compute mean/stdev SES."""
    groups: Dict[str, List[Dict]] = {}
    for r in results:
        key = f"{r['model']}__{r['flow']}"
        groups.setdefault(key, []).append(r)

    summary = {}
    for key, runs in sorted(groups.items()):
        ses_values = [r["ses"]["ses"] for r in runs if "ses" in r]
        summary[key] = {
            "n_runs": len(runs),
            "ses_mean": round(statistics.mean(ses_values), 4) if ses_values else None,
            "ses_stdev": round(statistics.stdev(ses_values), 4) if len(ses_values) >= 2 else None,
        }

    return summary


def select_top_models(results: List[Dict], top_n: int = 3) -> List[str]:
    """Select top N models by mean SES from Phase 1 results."""
    model_summary = aggregate_by_model(results)
    ranked = sorted(
        model_summary.items(),
        key=lambda x: x[1].get("ses_mean") or 0,
        reverse=True,
    )
    return [model for model, _ in ranked[:top_n]]


def print_summary(phase: str) -> None:
    """Print formatted summary table."""
    results = load_phase_results(phase)
    if not results:
        print(f"No results found for {phase}")
        return

    print(f"\n{'='*60}")
    print(f"Phase: {phase} — {len(results)} completed experiments")
    print(f"{'='*60}")

    if phase == "phase1":
        summary = aggregate_by_model(results)
        print(f"\n{'Model':<20} {'N':>3} {'SES Mean':>10} {'SES Std':>10} {'Best ddG':>10} {'Time(s)':>8}")
        print("-" * 65)
        for model, s in sorted(summary.items(), key=lambda x: x[1].get("ses_mean") or 0, reverse=True):
            print(f"{model:<20} {s['n_done']:>3} {s['ses_mean'] or 'N/A':>10} "
                  f"{s['ses_stdev'] or 'N/A':>10} {s['best_ddg_mean'] or 'N/A':>10} "
                  f"{s['mean_elapsed_s']:>8.0f}")
    else:
        summary = aggregate_by_model_flow(results)
        print(f"\n{'Model__Flow':<35} {'N':>3} {'SES Mean':>10} {'SES Std':>10}")
        print("-" * 62)
        for key, s in sorted(summary.items(), key=lambda x: x[1].get("ses_mean") or 0, reverse=True):
            print(f"{key:<35} {s['n_runs']:>3} {s['ses_mean'] or 'N/A':>10} "
                  f"{s['ses_stdev'] or 'N/A':>10}")


if __name__ == "__main__":
    import sys
    phase = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    print_summary(phase)
