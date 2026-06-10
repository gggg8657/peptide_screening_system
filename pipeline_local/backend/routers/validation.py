"""Validation endpoints — 규칙 기반 검증 및 수학적 검증.

P1-4 (2026-05-13): /validate/* 응답에 confidence_grade 자동 주입.
  - /validate/selected  → grade "B" (PyRosetta ddG, ideal coord 한계 VR-cycle-08)
  - /validate/unified   → grade "B" (복합 검증)
  - /validation/run     → grade "B" (수학적 검증)
  근거: pharmacology_guards.ENDPOINT_CONFIDENCE
"""
from __future__ import annotations

import json
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from pipeline_local.backend.state import (
    find_dashboard_archive,
    VALIDATION_DIR,
    EXP_LOG,
    MAX_VALIDATION_BATCH,
    VALIDATION_TIMEOUT_SEC,
    read_status,
    validation_executor,
)
from pipeline_local.scripts.pharmacology_guards import attach_confidence

router = APIRouter()


def _load_experiment_records() -> list:
    from pyrosetta_flow.ranking import load_experiment_records
    return load_experiment_records(EXP_LOG)


# ---------------------------------------------------------------------------
# 규칙 기반 검증 (ddG / clashScore / totalScore 임계값)
# ---------------------------------------------------------------------------

def _validate_candidates(candidate_ids: list[str], run_id: str | None = None) -> dict:
    if run_id:
        archive_path = find_dashboard_archive(run_id)
        if archive_path is None:
            return {"error": "유효하지 않은 run_id 또는 아카이브 없음", "results": []}
        data = json.loads(archive_path.read_text(encoding="utf-8"))
        all_candidates = data.get("candidates", [])
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
        ddg   = float(cand.get("ddG", 999.0))
        clash = float(cand.get("clashScore", 999.0))
        total = float(cand.get("totalScore", 0.0))

        checks.append({"rule": "ddG <= -5.0 kcal/mol",   "value": ddg,   "passed": ddg   <= -5.0})
        checks.append({"rule": "clashScore <= 10",        "value": clash, "passed": clash <= 10.0})
        checks.append({"rule": "totalScore <= -300 REU",  "value": total, "passed": total <= -300.0})

        all_passed = all(c["passed"] for c in checks)
        results.append({
            "id":         cid,
            "validation": "pass" if all_passed else "fail",
            "checks":     checks,
        })

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = VALIDATION_DIR / f"validation_{ts}.json"
    out_path.write_text(
        json.dumps({"timestamp": ts, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"results": results, "saved_to": str(out_path)}


# ---------------------------------------------------------------------------
# 수학적 검증 (통계 기반, 스레드풀 실행)
# ---------------------------------------------------------------------------

def _run_math_validation_sync(body: dict) -> dict:
    from backend.validation_facade import validate_batch
    sequences = body.get("candidate_sequences", [])
    top_k     = body.get("top_k", 3)
    if not isinstance(sequences, list) or not sequences:
        return {"error": "candidate_sequences 는 비어 있지 않은 문자열 배열이어야 합니다."}
    if len(sequences) > MAX_VALIDATION_BATCH:
        return {"error": f"배치 크기 초과 ({len(sequences)}). 최대 {MAX_VALIDATION_BATCH}개."}

    records = _load_experiment_records()
    result  = validate_batch(sequences, records, top_k=top_k)

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
        return {"error": f"검증 타임아웃 ({VALIDATION_TIMEOUT_SEC}초)"}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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
        detail="검증 결과 없음. POST /api/validation/run 을 먼저 실행하세요.",
    )


@router.post("/validation/run")
def run_math_validation(body: dict):
    """수학적 검증 (통계 기반) 실행.

    ⚠️ confidence_grade "B": in-silico 추정값. 임상 결과 대체 불가.
    """
    result = _run_math_validation(body)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return attach_confidence(result, "/validation/run")


@router.post("/validate/selected")
def validate_selected(body: dict):
    """후보 목록을 ddG/clashScore/totalScore 기준으로 검증한다.

    ⚠️ confidence_grade "B": ddG는 PyRosetta ref2015 (ideal coord 한계, VR-cycle-08).
    상대 비교만 유효. 임상 binding energy와 직결되지 않음.
    """
    ids    = body.get("candidate_ids", [])
    run_id = body.get("run_id")
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail="candidate_ids 는 비어 있지 않은 배열이어야 합니다.")
    raw = _validate_candidates(ids, run_id=run_id)
    return attach_confidence(raw, "/validate/selected")


@router.post("/validate/unified")
def validate_unified_endpoint(body: dict):
    """복합 검증 — 물리화학적 특성 + 구조 검증 통합 실행.

    ⚠️ confidence_grade "B": in-silico 추정값. 임상 결과 대체 불가.
    """
    from backend.validation_facade import validate_unified
    raw = validate_unified(
        sequences=body.get("sequences", []),
        criteria=body.get("criteria"),
        threshold_overrides=body.get("thresholds"),
        reference=body.get("reference", "AGCKNFFWKTFTSC"),
    )
    return attach_confidence(raw, "/validate/unified")
