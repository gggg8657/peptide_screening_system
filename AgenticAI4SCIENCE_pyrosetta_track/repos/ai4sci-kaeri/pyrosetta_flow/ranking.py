from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def append_experiment_records(log_path: Path, records: List[Dict[str, Any]]) -> None:
    """Append experiment records to JSONL log."""
    if not records:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        for row in records:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_experiment_records(log_path: Path) -> List[Dict[str, Any]]:
    """Load experiment records from JSONL log."""
    if not log_path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def extract_historical_sequences(records: List[Dict[str, Any]]) -> set[str]:
    """Extract all previously attempted sequences for cross-run deduplication."""
    return {
        r["sequence"]
        for r in records
        if r.get("record_type") == "candidate" and r.get("sequence")
    }


def summarize_top_hits(records: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """Return top-N successful candidates sorted by ddG for planner context."""
    successes = [
        r for r in records
        if r.get("record_type") == "candidate"
        and r.get("status") == "success"
        and float(r.get("ddg", 999)) < 0
    ]
    ranked = sorted(successes, key=lambda r: float(r.get("ddg", 999)))[:top_n]
    return [
        {
            "sequence": r["sequence"],
            "ddg": round(float(r["ddg"]), 2),
            "run_id": r.get("run_id", ""),
            "iteration": r.get("iteration", 0),
        }
        for r in ranked
    ]


def build_historical_candidates(records: List[Dict[str, Any]], limit: int = 200) -> List[Dict[str, Any]]:
    """Build aggregated ranking list from success/failure experiment records."""
    candidate_rows: List[Dict[str, Any]] = [r for r in records if r.get("record_type") == "candidate"]

    def _sort_key(row: Dict[str, Any]) -> tuple:
        status = row.get("status", "failed")
        is_failed = 0 if status == "success" else 1
        ddg = float(row.get("ddg", 999.0))
        return (is_failed, ddg)

    ranked = sorted(candidate_rows, key=_sort_key)[:limit]
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(ranked, start=1):
        status = row.get("status", "failed")
        fail_reason = row.get("error_summary", "") if status != "success" else row.get("fail_reason", "")
        ddg = float(row.get("ddg", 0.0))
        out.append(
            {
                "rank": idx,
                "id": row.get("candidate_id", f"log_{idx:03d}"),
                "sequence": row.get("sequence", ""),
                "ddG": ddg,
                "totalScore": float(row.get("total_score", 0.0)),
                "clashScore": float(row.get("clash_score", 0.0)),
                "finalScore": round(-ddg, 3) if ddg < 0 else 0.0,
                "result": "PASS" if status == "success" else "FAIL",
                "failReason": fail_reason,
                "runId": row.get("run_id", ""),
            }
        )
    return out
