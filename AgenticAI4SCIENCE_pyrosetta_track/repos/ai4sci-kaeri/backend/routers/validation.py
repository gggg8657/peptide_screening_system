"""Validation endpoints (rule-based, math, unified)."""
from __future__ import annotations

import json
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.state import (
    ARCHIVE_DIR,
    VALIDATION_DIR,
    EXP_LOG,
    MAX_VALIDATION_BATCH,
    VALIDATION_TIMEOUT_SEC,
    read_status,
    validation_executor,
)

router = APIRouter()


def _load_experiment_records() -> list:
    from pyrosetta_flow.ranking import load_experiment_records
    return load_experiment_records(EXP_LOG)


# ── Rule-based validation on pipeline candidates ────────────────────────────

def _validate_candidates(candidate_ids: list[str], run_id: str | None = None) -> dict:
    if run_id:
        archive_path = (ARCHIVE_DIR / f"{run_id}_dashboard.json").resolve()
        if not str(archive_path).startswith(str(ARCHIVE_DIR.resolve())):
            return {"error": "Invalid run_id", "results": []}
        if archive_path.exists():
            data = json.loads(archive_path.read_text(encoding="utf-8"))
            all_candidates = data.get("candidates", [])
        else:
            all_candidates = []
    else:
        status = read_status()
        all_candidates = status.get("candidates", [])
    cand_map = {c["id"]: c for c in all_candidates}

    results = []
    for cid in candidate_ids:
        cand = cand_map.get(cid)
        if cand is None:
            results.append({"id": cid, "validation": "not_found", "checks": []})
            continue

        checks = []
        ddg = float(cand.get("ddG", 999.0))
        clash = float(cand.get("clashScore", 999.0))
        total = float(cand.get("totalScore", 0.0))

        checks.append({"rule": "ddG <= -5.0 kcal/mol", "value": ddg, "passed": ddg <= -5.0})
        checks.append({"rule": "clashScore <= 10", "value": clash, "passed": clash <= 10.0})
        checks.append({"rule": "totalScore <= -300 REU", "value": total, "passed": total <= -300.0})

        all_passed = all(c["passed"] for c in checks)
        results.append({
            "id": cid,
            "validation": "pass" if all_passed else "fail",
            "checks": checks,
        })

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = VALIDATION_DIR / f"validation_{ts}.json"
    out_path.write_text(
        json.dumps({"timestamp": ts, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"results": results, "saved_to": str(out_path)}


# ── Math validation (statistical) ──────────────────────────────────────────

def _run_math_validation_sync(body: dict) -> dict:
    from backend.validation_facade import validate_batch
    sequences = body.get("candidate_sequences", [])
    top_k = body.get("top_k", 3)
    if not isinstance(sequences, list) or not sequences:
        return {"error": "candidate_sequences must be a non-empty array of sequence strings"}
    if len(sequences) > MAX_VALIDATION_BATCH:
        return {"error": f"Too many sequences ({len(sequences)}). Max batch size is {MAX_VALIDATION_BATCH}."}

    records = _load_experiment_records()
    result = validate_batch(sequences, records, top_k=top_k)

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    latest = VALIDATION_DIR / "validation_results.json"
    latest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    history = VALIDATION_DIR / "validation_history.jsonl"
    with history.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")
    return result


def _run_math_validation(body: dict) -> dict:
    future = validation_executor.submit(_run_math_validation_sync, body)
    try:
        return future.result(timeout=VALIDATION_TIMEOUT_SEC)
    except FuturesTimeoutError:
        future.cancel()
        return {"error": f"Validation timed out after {VALIDATION_TIMEOUT_SEC}s"}


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/validation/criteria")
def get_criteria():
    from backend.validation_facade import get_criteria_registry
    return get_criteria_registry()


@router.get("/validation/results")
def get_validation_results():
    latest = VALIDATION_DIR / "validation_results.json"
    if latest.exists():
        try:
            return json.loads(latest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    raise HTTPException(
        status_code=404,
        detail="No validation results found. Run POST /api/validation/run first.",
    )


@router.post("/validation/run")
def run_math_validation(body: dict):
    result = _run_math_validation(body)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/validate/selected")
def validate_selected(body: dict):
    ids = body.get("candidate_ids", [])
    run_id = body.get("run_id")
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail="candidate_ids must be a non-empty array")
    return _validate_candidates(ids, run_id=run_id)


@router.post("/validate/unified")
def validate_unified_endpoint(body: dict):
    from backend.validation_facade import validate_unified
    return validate_unified(
        sequences=body.get("sequences", []),
        criteria=body.get("criteria"),
        threshold_overrides=body.get("thresholds"),
        reference=body.get("reference", "AGCKNFFWKTFTSC"),
    )
