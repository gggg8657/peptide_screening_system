"""Load experiment run outputs into pandas DataFrame for analysis."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import pandas as pd  # noqa: F811

OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent / "outputs"


def load_runs(phase: str, outputs_dir: Optional[Path] = None) -> "pd.DataFrame":
    """Load all completed runs from a phase into a DataFrame.

    Columns: model, flow, seed, ses, hit_rate, improvement, efficiency,
             diversity, robustness, best_ddg, n_hits, n_total, elapsed_s
    """
    import pandas as pd

    base = outputs_dir or OUTPUTS_DIR
    phase_dir = base / phase
    rows = []

    for run_dir in sorted(phase_dir.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("_"):
            continue

        status_file = run_dir / "status.json"
        ses_file = run_dir / "ses_score.json"

        if not status_file.exists():
            continue
        status = json.loads(status_file.read_text())
        if status.get("state") != "done":
            continue

        parts = run_dir.name.split("__")
        model = parts[0] if len(parts) >= 1 else "unknown"
        flow = parts[1] if len(parts) >= 2 else "sequential"
        seed = 0
        gate_mode = "static"
        for p in parts[2:]:
            if p.startswith("s") and p[1:].isdigit():
                seed = int(p.lstrip("s"))
            elif p in ("static", "adaptive"):
                gate_mode = p

        row = {"model": model, "flow": flow, "seed": seed, "elapsed_s": status.get("elapsed_s", 0)}

        if ses_file.exists():
            ses = json.loads(ses_file.read_text())
            row.update(ses)

        rows.append(row)

    return pd.DataFrame(rows)


def load_agent_logs(run_dir: str | Path) -> list[dict]:
    """Load all agent log JSONL files from a single run."""
    log_dir = Path(run_dir) / "agent_log"
    logs = []
    if not log_dir.exists():
        return logs

    for f in sorted(log_dir.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                logs.append(json.loads(line))

    return logs
