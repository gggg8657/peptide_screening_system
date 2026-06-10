"""Status & health endpoints."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.state import STATUS_FILE, ARCHIVE_DIR, read_status, atomic_write_json

router = APIRouter()
logger = logging.getLogger(__name__)
SERVICE_NAME = "ai4sci-kaeri-backend"
SERVICE_VERSION = "2.0.0"


class PipelineStatusUpdate(BaseModel):
    """Request body for POST /api/status — pipeline status push."""
    phase: Optional[str] = Field(None, description="Current pipeline phase")
    iteration: Optional[int] = Field(None, ge=0, description="Current iteration number")
    total_iterations: Optional[int] = Field(None, ge=0)
    candidates: Optional[list[dict[str, Any]]] = Field(None, description="Candidate list")
    started_at: Optional[str] = None
    completed: Optional[bool] = None
    run_id: Optional[str] = None
    agent_states: Optional[dict[str, Any]] = None

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Candidate 6-field enrichment helpers
# ---------------------------------------------------------------------------


def _get_selectivity_margins() -> Dict[str, Optional[float]]:
    """완료된 selectivity job에서 candidate_id → selectivity_margin 매핑을 빌드.

    selectivity.py의 _JOBS(in-memory) dict에서 completed job만 취합.
    가장 최근 job의 값이 이전 값을 덮어씀.
    """
    try:
        from backend.routers.selectivity import _JOBS  # type: ignore[import-untyped]
        margins: Dict[str, Optional[float]] = {}
        for job in _JOBS.values():
            if job.get("status") == "completed":
                for cand in job.get("candidates", []):
                    cid = cand.get("candidate_id")
                    if cid is not None:
                        margins[cid] = cand.get("selectivity_margin")
        return margins
    except Exception as exc:
        logger.debug("selectivity margin lookup 실패 (무시): %s", exc)
        return {}


def _enrich_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """candidate dict에 6개 필드를 on-the-fly 머지.

    이미 값(None이 아닌)이 있는 필드는 덮어쓰지 않음.

    6 필드:
      ① instability_index  — pharmacology.instability_index(seq)
      ② gravy              — pharmacology.gravy(seq)
      ③ net_charge_ph74    — admet.compute_admet(seq)["net_charge_ph74"]
      ④ selectivity_margin — selectivity job 결과 (완료된 job 기준)
      ⑤ fwkt_contact       — pharmacophore.compute_fwkt_contact(candidate)
      ⑥ chelator_site_available — pharmacophore.compute_chelator_site(seq)

    HEURISTIC 표시:
      ⑤, ⑥은 sequence-only 휴리스틱 (PDB 기반 검증 미수행).
      pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS 등록 참조.
    """
    if not candidates:
        return candidates

    # lazy import — API 서버 내에서만 호출되므로 순환 import 없음
    try:
        from backend.pharmacology import instability_index as _ii, gravy as _gravy
        _has_pharma = True
    except Exception as exc:
        logger.warning("backend.pharmacology import 실패: %s", exc)
        _has_pharma = False

    try:
        from backend.admet import compute_admet as _compute_admet
        _has_admet = True
    except Exception as exc:
        logger.warning("backend.admet import 실패: %s", exc)
        _has_admet = False

    try:
        from backend.pharmacophore import compute_fwkt_contact, compute_chelator_site
        _has_phcore = True
    except Exception as exc:
        logger.warning("backend.pharmacophore import 실패: %s", exc)
        _has_phcore = False

    # selectivity_margin 매핑 빌드 (job 완료된 것만)
    sel_margins = _get_selectivity_margins()

    enriched = []
    for cand in candidates:
        c = dict(cand)  # shallow copy — 원본 변경 없음
        seq: Optional[str] = c.get("sequence")

        # ① instability_index
        if c.get("instability_index") is None and seq and _has_pharma:
            try:
                c["instability_index"] = _ii(seq)
            except Exception as exc:
                logger.debug("instability_index 계산 실패 (cid=%s): %s", c.get("id"), exc)

        # ② gravy
        if c.get("gravy") is None and seq and _has_pharma:
            try:
                c["gravy"] = _gravy(seq)
            except Exception as exc:
                logger.debug("gravy 계산 실패 (cid=%s): %s", c.get("id"), exc)

        # ③ net_charge_ph74
        if c.get("net_charge_ph74") is None and seq and _has_admet:
            try:
                admet_result = _compute_admet(seq)
                c["net_charge_ph74"] = admet_result.get("net_charge_ph74")
            except Exception as exc:
                logger.debug("net_charge_ph74 계산 실패 (cid=%s): %s", c.get("id"), exc)

        # ④ selectivity_margin — selectivity job 완료된 것만 머지
        if c.get("selectivity_margin") is None:
            cid = c.get("id") or c.get("candidate_id")
            if cid and cid in sel_margins:
                c["selectivity_margin"] = sel_margins[cid]

        # ⑤ fwkt_contact (HEURISTIC)
        if c.get("fwkt_contact") is None and _has_phcore:
            try:
                c["fwkt_contact"] = compute_fwkt_contact(c)
            except Exception as exc:
                logger.debug("fwkt_contact 계산 실패 (cid=%s): %s", c.get("id"), exc)

        # ⑥ chelator_site_available (HEURISTIC)
        if c.get("chelator_site_available") is None and seq and _has_phcore:
            try:
                c["chelator_site_available"] = compute_chelator_site(seq)
            except Exception as exc:
                logger.debug("chelator_site_available 계산 실패 (cid=%s): %s", c.get("id"), exc)

        enriched.append(c)

    return enriched


@router.get("/status")
def get_status() -> Dict[str, Any]:
    """파이프라인 status 반환 — candidates에 6개 필드 on-the-fly 머지."""
    status = read_status()
    # candidates 필드가 있으면 6-field enrichment 적용
    if isinstance(status.get("candidates"), list):
        status["candidates"] = _enrich_candidates(status["candidates"])
    return status


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": time.time(),
    }


@router.post("/status")
def post_status(data: PipelineStatusUpdate):
    try:
        # 2026-06-09 D2/F04: 원자적 기록(temp+rename under flock) — torn-write 방지
        atomic_write_json(STATUS_FILE, data.model_dump(exclude_none=False))
        return {"ok": True}
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/runs")
def list_runs():
    if not ARCHIVE_DIR.exists():
        return {"runs": []}
    runs = []
    for f in sorted(ARCHIVE_DIR.glob("*_dashboard.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            runs.append({
                "run_id": data.get("run_id", f.stem),
                "started_at": data.get("started_at", ""),
                "completed": data.get("completed", False),
                "iteration": data.get("iteration", 0),
                "total_iterations": data.get("total_iterations", 0),
                "n_candidates": len(data.get("candidates", [])),
                "best_ddg": min(
                    (c.get("ddG", 999) for c in data.get("candidates", [])),
                    default=None,
                ),
                "label": data.get("label"),
                "llm_model": data.get("llm_model", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return {"runs": runs}


@router.get("/runs/{run_id}")
def get_archived_run(run_id: str):
    archive_path = (ARCHIVE_DIR / f"{run_id}_dashboard.json").resolve()
    if not str(archive_path).startswith(str(ARCHIVE_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid run_id")
    if not archive_path.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    try:
        return json.loads(archive_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
