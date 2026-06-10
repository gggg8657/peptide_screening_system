"""
stability.py — Stability Predictor API Router (U5 구현)
=======================================================
SSTR2 펩타이드 바인더 후보의 안정성 통합 평가 API 엔드포인트.

Endpoints:
    GET  /api/stability/predict?seq=<sequence>   단일 서열 평가
    POST /api/stability/batch                    배치 평가
    GET  /api/stability/result/{job_id}          비동기 결과 조회 (in-memory)
    GET  /api/stability/cand03                   8 후보 사전 평가 결과

⚠️ HEURISTIC — stability_predictor.compute_stability 와 동일 한계 적용.
   hl_score는 임상 반감기 절대값이 아닌 ranking score.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

router = APIRouter()

# 유효 아미노산 (canonical) + NCAA 표기 허용
_VALID_SEQ_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY\[\]a-z0-9]+$", re.IGNORECASE)
_MAX_BATCH = 100

# in-memory job store (prototype — 재시작 시 초기화)
_job_store: Dict[str, Dict[str, Any]] = {}

# 8 후보 사전 평가 결과 캐시 경로
_CAND8_JSON = Path("runs_local/stability/batch_8_candidates.json")


# ---------------------------------------------------------------------------
# Pydantic 모델
# ---------------------------------------------------------------------------

class StabilityResponse(BaseModel):
    """단일 서열 안정성 평가 응답."""
    seq_id: str
    sequence: str
    canonical_sequence: str
    mw: float
    gravy: float
    instability_index: float
    is_unstable: bool
    stability_class: str
    pi: float
    boman: Optional[float]
    charge_ph74: Optional[float]
    aliphatic_index: float
    protease_cleavage_sites: Dict[str, List[int]]
    admet_score: Dict[str, Any]
    nephrotox_risk: str
    hl_score_heuristic: float           # HEURISTIC ranking score (NOT half-life)
    hl_warnings: List[str]
    ncaa_warnings: List[str]
    surrogate_panel: Dict[str, Any]
    agreement_profile: Dict[str, Any]


class BatchRequest(BaseModel):
    """Batch 평가 요청 본문."""
    sequences: List[str]
    seq_ids: Optional[List[str]] = None
    modifications: Optional[List[List[str]]] = None

    @field_validator("sequences")
    @classmethod
    def validate_sequences(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("sequences must be non-empty")
        if len(v) > _MAX_BATCH:
            raise ValueError(f"Too many sequences ({len(v)}). Max batch size is {_MAX_BATCH}.")
        return v


class BatchResponse(BaseModel):
    """Batch 평가 응답."""
    n_total: int
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]


class AsyncJobResponse(BaseModel):
    """비동기 작업 응답."""
    job_id: str
    status: str                 # "pending" | "completed" | "error"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _load_stability_predictor():
    """stability_predictor 모듈 지연 임포트."""
    try:
        from pipeline_local.scripts.stability_predictor import (
            compute_stability,
            batch_evaluate,
            CANDIDATE_8,
            run_candidate8_batch,
        )
        return compute_stability, batch_evaluate, CANDIDATE_8, run_candidate8_batch
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"stability_predictor 모듈 로드 실패: {e}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stability/predict")
async def predict_single(seq: str) -> StabilityResponse:
    """단일 서열 안정성 평가.

    Query params:
        seq: 아미노산 서열 (canonical + NCAA 표기 허용)

    Returns:
        StabilityResponse
    """
    seq = seq.strip()
    if not seq:
        raise HTTPException(status_code=400, detail="seq 파라미터가 비어 있습니다.")
    if not _VALID_SEQ_RE.match(seq):
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 아미노산 서열: {seq[:50]!r}. 표준 1-letter code 또는 [NCAA] 표기만 허용.",
        )

    compute_stability, *_ = _load_stability_predictor()
    try:
        result = compute_stability(seq, seq_id=seq[:8])
    except Exception as e:
        logger.exception("[/stability/predict] 계산 실패")
        raise HTTPException(status_code=500, detail=f"계산 오류: {e}")

    return result.to_dict()


@router.post("/stability/batch")
async def predict_batch(body: BatchRequest) -> BatchResponse:
    """배치 서열 안정성 평가 (동기, 최대 100개).

    Body:
        sequences: 서열 목록
        seq_ids: 각 서열 ID (선택)
        modifications: 서열별 modification 목록 (선택)
    """
    _, batch_evaluate, *_ = _load_stability_predictor()
    try:
        result = batch_evaluate(
            body.sequences,
            body.seq_ids,
            body.modifications,
        )
    except Exception as e:
        logger.exception("[/stability/batch] 배치 평가 실패")
        raise HTTPException(status_code=500, detail=f"배치 계산 오류: {e}")

    return BatchResponse(
        n_total=result.n_total,
        results=[r.to_dict() for r in result.results],
        summary=result.summary,
    )


@router.post("/stability/batch/async")
async def predict_batch_async(
    body: BatchRequest,
    background_tasks: BackgroundTasks,
) -> AsyncJobResponse:
    """배치 서열 안정성 평가 (비동기 — 즉시 job_id 반환).

    결과는 GET /api/stability/result/{job_id} 로 조회.
    """
    _, batch_evaluate, *_ = _load_stability_predictor()

    job_id = str(uuid.uuid4())[:8]
    _job_store[job_id] = {"status": "pending", "result": None, "error": None}

    def _run():
        try:
            r = batch_evaluate(body.sequences, body.seq_ids, body.modifications)
            _job_store[job_id] = {
                "status": "completed",
                "result": r.to_dict(),
                "error": None,
            }
        except Exception as e:
            _job_store[job_id] = {"status": "error", "result": None, "error": str(e)}

    background_tasks.add_task(_run)

    return AsyncJobResponse(job_id=job_id, status="pending")


@router.get("/stability/result/{job_id}")
async def get_job_result(job_id: str) -> AsyncJobResponse:
    """비동기 배치 평가 결과 조회.

    Args:
        job_id: predict_batch_async 에서 반환된 job ID

    Returns:
        AsyncJobResponse (status: pending|completed|error)
    """
    if job_id not in _job_store:
        raise HTTPException(status_code=404, detail=f"job_id={job_id!r} 없음 또는 만료됨")
    job = _job_store[job_id]
    return AsyncJobResponse(
        job_id=job_id,
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
    )


@router.get("/stability/cand03")
async def get_cand03_results() -> BatchResponse:
    """본 프로젝트 8 후보 사전 평가 결과 반환.

    사전 계산된 결과가 있으면 캐시에서 즉시 반환.
    없으면 실시간 계산 후 저장.

    8 후보:
        SST14_ref, cand03, T3_1~T3_5, var12_dThr
    """
    # 캐시 확인
    if _CAND8_JSON.exists():
        try:
            with open(_CAND8_JSON, encoding="utf-8") as f:
                cached = json.load(f)
            return BatchResponse(
                n_total=cached["n_total"],
                results=cached["results"],
                summary=cached["summary"],
            )
        except Exception as e:
            logger.warning("[/stability/cand03] 캐시 로드 실패 %s, 재계산", e)

    # 실시간 계산
    _, _, _, run_candidate8_batch = _load_stability_predictor()
    try:
        result = run_candidate8_batch(Path("runs_local/stability"))
    except Exception as e:
        logger.exception("[/stability/cand03] 실시간 계산 실패")
        raise HTTPException(status_code=500, detail=f"8 후보 계산 오류: {e}")

    return BatchResponse(
        n_total=result.n_total,
        results=[r.to_dict() for r in result.results],
        summary=result.summary,
    )
