"""
flexpepdock.py — FlexPepDock Manual Selectivity BE 라우터
==========================================================
사용자가 수기로 FlexPepDock 정밀 도킹 + Selectivity 계산을 트리거하는 엔드포인트.

사용자 결정 (2026-05-15):
  - 동시 실행: 1개 lock (운영 1인 가정)
  - 결과 retention: 영구 보관
  - ETA 계산: 동적 학습 (이전 완료 job 평균 기반, 기본 30min × receptor 수)
  - wetlab 통합: 결과 페이지에서 직접 wetlab order 생성 (flexpepdock_job_id 전달)

Endpoints:
  POST   /api/flexpepdock/jobs
  GET    /api/flexpepdock/jobs
  GET    /api/flexpepdock/jobs/{job_id}
  GET    /api/flexpepdock/jobs/{job_id}/results
  GET    /api/flexpepdock/jobs/{job_id}/ensemble.tar.gz
  DELETE /api/flexpepdock/jobs/{job_id}
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parents[3]  # SST14-M_scr

# pipeline_local 모듈 접근을 위해 repo root를 sys.path에 추가
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline_local.scripts.flexpepdock_worker import (
    JOBS_DIR,
    LOCK_FILE,
    build_ensemble_tar,
    estimate_eta,
    find_queued_jobs,
    get_receptor_pdb_path,
    preflight_check,
    read_job,
    read_status_file,
    write_status,
    _RECEPTOR_PDB_IDS,
    _pid_alive,
)

router = APIRouter()
logger = logging.getLogger(__name__)

_WORKER_PROC: Optional[subprocess.Popen] = None  # lifespan에서 관리

# ---------------------------------------------------------------------------
# Pydantic 스키마
# ---------------------------------------------------------------------------


class FlexPepDockConfig(BaseModel):
    """FlexPepDock 실행 파라미터."""

    cycles: int = Field(default=10, ge=1, le=200, description="FastRelax 사이클 수")
    nstruct: int = Field(default=50, ge=1, le=500, description="앙상블 구조 수")
    flex_pep_freedom: Literal["low", "med", "high"] = Field(
        default="med", description="펩타이드 유연성 수준"
    )
    ddg_cycle: int = Field(default=5, ge=1, le=50, description="ddG 계산 반복 수")


class FlexPepDockJobRequest(BaseModel):
    """POST /api/flexpepdock/jobs 요청 본문."""

    sequence: str = Field(
        ...,
        min_length=14,
        max_length=14,
        description="14aa 펩타이드 시퀀스 (Cys3-Cys14 SS bond)",
    )
    receptors: list[str] = Field(
        ...,
        min_length=1,
        description="도킹 대상 수용체 목록 (SSTR1~SSTR5)",
    )
    config: FlexPepDockConfig = Field(default_factory=FlexPepDockConfig)

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, v: str) -> str:
        """시퀀스 길이·아미노산·Cys 위치 검증."""
        seq = v.strip().upper()
        valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
        invalid = [c for c in seq if c not in valid_aa]
        if invalid:
            raise ValueError(f"유효하지 않은 아미노산: {invalid}")
        if seq[2] != "C":
            raise ValueError(f"Cys3 위치({seq[2]})가 C가 아님 — SS bond 위반")
        if seq[13] != "C":
            raise ValueError(f"Cys14 위치({seq[13]})가 C가 아님 — SS bond 위반")
        return seq

    @field_validator("receptors")
    @classmethod
    def validate_receptors(cls, v: list[str]) -> list[str]:
        """수용체 이름 대문자 정규화 + SSTR1-5 범위 확인."""
        valid = set(_RECEPTOR_PDB_IDS.keys())
        normalized = [r.strip().upper() for r in v]
        unknown = [r for r in normalized if r not in valid]
        if unknown:
            raise ValueError(f"알 수 없는 수용체: {unknown}. 유효: {sorted(valid)}")
        return normalized


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------


def _get_queue_position(job_id: str) -> int:
    """job_id의 큐 순위(1-indexed)를 반환한다. 큐에 없으면 0."""
    queued = find_queued_jobs()
    try:
        return queued.index(job_id) + 1
    except ValueError:
        return 0


def _read_result(job_id: str) -> Optional[dict[str, Any]]:
    """result.json을 읽어 반환한다."""
    p = JOBS_DIR / job_id / "result.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _job_summary(job_id: str) -> Optional[dict[str, Any]]:
    """job.json + status.json을 합쳐 요약 dict를 반환한다."""
    job = read_job(job_id)
    status = read_status_file(job_id)
    if job is None or status is None:
        return None
    return {
        "job_id": job_id,
        "sequence": job.get("sequence", ""),
        "receptors": job.get("receptors", []),
        "config": job.get("config", {}),
        "status": status.get("state", "unknown"),
        "progress": status.get("progress", 0.0),
        "eta_seconds": status.get("eta_seconds", 0),
        "created_at": job.get("created_at", ""),
        "started_at": status.get("started_at", ""),
        "finished_at": status.get("finished_at", ""),
        "error_message": status.get("error_message", ""),
    }


def _is_worker_running() -> bool:
    """워커 프로세스(또는 lock holder)가 실행 중인지 확인한다."""
    if LOCK_FILE.exists():
        try:
            data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
            if pid and _pid_alive(pid):
                return True
        except (json.JSONDecodeError, ValueError, OSError):
            pass
    return False


def _ensure_worker_running() -> None:
    """워커 프로세스가 없으면 subprocess로 기동한다."""
    global _WORKER_PROC
    if _WORKER_PROC is not None and _WORKER_PROC.poll() is None:
        return  # 이미 실행 중

    # subprocess로 워커 실행 (별도 프로세스, daemon처럼 동작)
    worker_script = _REPO_ROOT / "pipeline_local" / "scripts" / "flexpepdock_worker.py"
    if not worker_script.exists():
        logger.error("워커 스크립트 없음: %s", worker_script)
        return

    python_exe = sys.executable
    try:
        _WORKER_PROC = subprocess.Popen(
            [python_exe, str(worker_script)],
            env={**os.environ, "PYTHONPATH": str(_REPO_ROOT)},
        )
        logger.info("FlexPepDock 워커 기동 (PID=%d)", _WORKER_PROC.pid)
    except OSError as exc:
        logger.error("워커 기동 실패: %s", exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/flexpepdock/jobs", status_code=201)
def create_flexpepdock_job(body: FlexPepDockJobRequest) -> dict[str, Any]:
    """FlexPepDock job을 등록하고 큐에 추가한다.

    - 동시 실행 1개 제한 (운영 1인 가정)
    - 사전 검증 (시퀀스 · 수용체 PDB · PyRosetta)
    - ETA 동적 추정 (이전 완료 이력 기반)
    """
    # 사전 검증
    ok, err = preflight_check(body.sequence, body.receptors)
    if not ok:
        raise HTTPException(status_code=422, detail=f"Pre-flight 검증 실패: {err}")

    # Job ID 생성
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    nstruct = body.config.nstruct
    n_receptors = len(body.receptors)
    eta = estimate_eta(n_receptors, nstruct)

    # job.json 저장
    job_data: dict[str, Any] = {
        "job_id": job_id,
        "sequence": body.sequence,
        "receptors": body.receptors,
        "config": {
            "cycles": body.config.cycles,
            "nstruct": nstruct,
            "flex_pep_freedom": body.config.flex_pep_freedom,
            "ddg_cycle": body.config.ddg_cycle,
        },
        "created_at": created_at,
    }
    (job_dir / "job.json").write_text(
        json.dumps(job_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # status.json 초기화
    write_status(job_id, state="queued", eta_seconds=eta)

    queue_position = _get_queue_position(job_id)

    # 워커 기동 확인 (필요시 재기동)
    _ensure_worker_running()

    logger.info(
        "FlexPepDock job 등록: %s (seq=%s, receptors=%s, eta=%ds)",
        job_id, body.sequence, body.receptors, eta,
    )

    return {
        "job_id": job_id,
        "eta_seconds": eta,
        "queue_position": queue_position,
    }


@router.get("/flexpepdock/jobs")
def list_flexpepdock_jobs(
    status: Optional[str] = None,
) -> dict[str, Any]:
    """등록된 모든 FlexPepDock job 목록을 반환한다.

    Query:
        status (optional): queued|running|done|failed 필터
    """
    if not JOBS_DIR.exists():
        return {"jobs": []}

    jobs: list[dict[str, Any]] = []
    valid_statuses = {"queued", "running", "done", "failed", "cancelling"}

    for job_dir in sorted(JOBS_DIR.iterdir(), key=lambda d: d.stat().st_mtime if d.is_dir() else 0):
        if not job_dir.is_dir():
            continue
        if job_dir.name.startswith("."):
            continue

        summary = _job_summary(job_dir.name)
        if summary is None:
            continue

        if status and summary.get("status") not in valid_statuses:
            continue
        if status and summary.get("status") != status:
            continue

        jobs.append(summary)

    return {"jobs": jobs}


@router.get("/flexpepdock/jobs/{job_id}")
def get_flexpepdock_job(job_id: str) -> dict[str, Any]:
    """특정 job의 전체 상태를 반환한다."""
    summary = _job_summary(job_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} 없음")

    # queue_position 추가
    if summary["status"] == "queued":
        summary["queue_position"] = _get_queue_position(job_id)
    else:
        summary["queue_position"] = 0

    return summary


@router.get("/flexpepdock/jobs/{job_id}/results")
def get_flexpepdock_results(job_id: str) -> dict[str, Any]:
    """완료된 job의 Selectivity 결과를 반환한다.

    Response:
        selectivity_matrix: list[{receptor, dG_kcal_mol, interface_score, pass}]
        selectivity_index:  float
        pdb_paths:          list[str]
    """
    status = read_status_file(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} 없음")

    state = status.get("state", "")
    if state != "done":
        raise HTTPException(
            status_code=202,
            detail=f"Job {job_id} 상태: {state} — 완료 후 결과 조회 가능",
        )

    result = _read_result(job_id)
    if result is None:
        raise HTTPException(
            status_code=500,
            detail=f"Job {job_id} result.json 없음 — 워커 오류 가능성",
        )

    return result


@router.get("/flexpepdock/jobs/{job_id}/ensemble.tar.gz")
def download_ensemble(job_id: str) -> FileResponse:
    """ensemble PDB tar.gz를 다운로드한다."""
    status = read_status_file(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} 없음")

    if status.get("state") != "done":
        raise HTTPException(status_code=202, detail="Job 아직 완료 안 됨")

    # tar.gz 생성 (캐시: 이미 있으면 재사용)
    tar_path = JOBS_DIR / job_id / "ensemble.tar.gz"
    if not tar_path.exists():
        tar_path = build_ensemble_tar(job_id)
    if tar_path is None or not tar_path.exists():
        raise HTTPException(status_code=404, detail="ensemble PDB 없음")

    return FileResponse(
        path=str(tar_path),
        media_type="application/gzip",
        filename=f"flexpepdock_{job_id}_ensemble.tar.gz",
    )


@router.delete("/flexpepdock/jobs/{job_id}", status_code=200)
def delete_flexpepdock_job(job_id: str) -> dict[str, Any]:
    """Job을 취소 또는 삭제한다.

    상태별 동작:
        queued  → 큐에서 제거 (status: failed)
        running → cancelling 으로 전환 (워커가 다음 수용체에서 감지 후 종료)
        done/failed → 영구 보관 정책 — no-op (400 반환)
    """
    status = read_status_file(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} 없음")

    state = status.get("state", "")

    if state == "queued":
        write_status(
            job_id,
            state="failed",
            error_message="사용자 삭제 요청 (queued)",
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        logger.info("[%s] queued job 삭제", job_id)
        return {"ok": True, "job_id": job_id, "action": "removed_from_queue"}

    if state == "running":
        # cancelling 상태로 전환 → 워커 폴링에서 감지
        write_status(
            job_id,
            state="cancelling",
            progress=status.get("progress", 0.0),
            eta_seconds=0,
            error_message="사용자 취소 요청",
        )
        logger.info("[%s] running job 취소 요청", job_id)
        return {"ok": True, "job_id": job_id, "action": "cancellation_requested"}

    if state in ("done", "failed", "cancelling"):
        # 영구 보관 정책 — 실제 삭제 불가
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} 상태 '{state}' — 영구 보관 정책으로 삭제 불가",
        )

    raise HTTPException(status_code=400, detail=f"알 수 없는 상태: {state}")
