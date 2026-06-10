"""Status & health endpoints — 파이프라인 상태 조회/갱신."""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from pipeline_local.backend.state import (
    STATUS_FILE,
    read_status,
    list_archive_dashboard_files,
    find_dashboard_archive,
)

router = APIRouter()


class PipelineStatusUpdate(BaseModel):
    """POST /api/status — 파이프라인 상태 푸시 요청 바디."""
    phase:            Optional[str]              = Field(None, description="현재 파이프라인 단계")
    iteration:        Optional[int]              = Field(None, ge=0, description="현재 반복 번호")
    total_iterations: Optional[int]              = Field(None, ge=0)
    candidates:       Optional[list[dict[str, Any]]] = Field(None, description="후보 목록")
    started_at:       Optional[str]              = None
    completed:        Optional[bool]             = None
    run_id:           Optional[str]              = None
    agent_states:     Optional[dict[str, Any]]   = None

    model_config = {"extra": "allow"}


@router.get("/status")
def get_status():
    """pipeline_status.json 의 최신 내용을 반환한다."""
    return read_status()


@router.get("/health")
def health():
    """서버 헬스 체크."""
    return {"status": "ok", "timestamp": time.time(), "mode": "local"}


@router.post("/status")
def post_status(data: PipelineStatusUpdate):
    """파이프라인 프로세스가 상태를 밀어 넣는 엔드포인트."""
    try:
        STATUS_FILE.write_text(
            json.dumps(data.model_dump(exclude_none=False), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"ok": True}
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/runs")
def list_runs():
    """아카이브 디렉터리(들)의 완료된 실험 목록을 반환한다.

    기본: ``runs/pyrosetta_flow/archives`` 및 ``runs_local/archives`` 병합.
    """
    files = list_archive_dashboard_files()
    if not files:
        return {"runs": []}
    runs = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            runs.append({
                "run_id":           data.get("run_id", f.stem),
                "started_at":       data.get("started_at", ""),
                "completed":        data.get("completed", False),
                "iteration":        data.get("iteration", 0),
                "total_iterations": data.get("total_iterations", 0),
                "n_candidates":     len(data.get("candidates", [])),
                "best_ddg":         min(
                    (c.get("ddG", 999) for c in data.get("candidates", [])),
                    default=None,
                ),
                "label":      data.get("label"),
                "llm_model":  data.get("llm_model", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return {"runs": runs}


@router.get("/runs/{run_id}")
def get_archived_run(run_id: str):
    """지정된 run_id 의 아카이브 대시보드 JSON을 반환한다."""
    archive_path = find_dashboard_archive(run_id)
    if archive_path is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} 을 찾을 수 없습니다.")
    try:
        return json.loads(archive_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
