"""
FastAPI Application — LOCAL MODE
==================================
pipeline_local 전용 백엔드 서버.
NIM API 없이 로컬 GPU 모델만 사용하는 파이프라인 모니터링 API.

실행 방법:
    # 권장 (모듈 실행, REPO_ROOT 기준)
    cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
    python -m pipeline_local.backend.main

    # uvicorn 직접 실행
    uvicorn pipeline_local.backend.main:app --host 0.0.0.0 --port 8787 --reload
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# ---------------------------------------------------------------------------
# 로컬 모드 환경 변수 — uvicorn이 import 하기 전에 설정
# ---------------------------------------------------------------------------
os.environ.setdefault("OLLAMA_HOST", "127.0.0.1:11435")
os.environ.setdefault("API_PORT", "8787")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pipeline_local.backend.routers import (
    status,
    analysis,
    validation,
    experiment,
    admet,
    static,
    settings,
    rcsb,
    selectivity,
    ui_integrations,
)
from pipeline_local.backend.state import PORT

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup 훅에서 orphan worker PID 파일 정리
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI 애플리케이션 lifespan 컨텍스트.

    startup: stale(dead) worker PID 파일 + lock 파일 자동 정리.
    shutdown: 별도 작업 없음 (worker는 별도 프로세스이므로 여기서 관리하지 않음).
    """
    # --- startup ---
    try:
        from pipeline_local.scripts.flexpepdock_worker import (
            cleanup_stale_worker_pid_files,
        )
        cleaned = cleanup_stale_worker_pid_files()
        if cleaned:
            logger.warning(
                "[startup] orphan worker PID %d건 정리: %s", len(cleaned), cleaned
            )
        else:
            logger.info("[startup] orphan worker PID 없음 — 정리 불필요")
    except Exception as exc:  # noqa: BLE001
        # 정리 실패가 서버 기동을 막아서는 안 됨
        logger.error("[startup] orphan cleanup 실패 (무시): %s", exc)

    yield  # 애플리케이션 실행

    # --- shutdown ---
    # worker 프로세스는 SIGTERM으로 별도 종료하므로 여기서는 아무 것도 하지 않음.


def create_app() -> FastAPI:
    """FastAPI 애플리케이션을 생성하고 구성한다.

    라우터 prefix 구조:
        /api/          — 현재 local 파이프라인 (기본)
        /api/v1/...    — 향후 멀티 파이프라인 확장 예정

    Vite 프록시는 localhost:5173 → localhost:8787 로 포워딩한다.
    """
    app = FastAPI(
        title="AI4Sci Pipeline Monitor — Local Mode",
        description=(
            "SSTR2 방사성의약품 후보 스크리닝 파이프라인 모니터링 API (NIM API 미사용 로컬 버전)"
        ),
        version="2.1.0-local",
        lifespan=_lifespan,
    )

    # CORS — Vite 개발 서버 및 백엔드 직접 접근 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:8787",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8787",
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    # ---------------------------------------------------------------------------
    # 전역 예외 핸들러 — 일관된 JSON 오류 응답 형식
    # ---------------------------------------------------------------------------

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error":       "InternalServerError",
                "detail":      "내부 서버 오류",
                "status_code": 500,
            },
        )

    from fastapi.exceptions import HTTPException as FastAPIHTTPException

    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error":       "HTTPException",
                "detail":      exc.detail,
                "status_code": exc.status_code,
            },
        )

    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error":       "ValidationError",
                "detail":      str(exc),
                "status_code": 422,
            },
        )

    # ---------------------------------------------------------------------------
    # 라우터 등록 — 모두 /api 프리픽스 아래
    # ---------------------------------------------------------------------------
    app.include_router(status.router,     prefix="/api", tags=["status"])
    app.include_router(analysis.router,   prefix="/api", tags=["analysis"])
    app.include_router(validation.router, prefix="/api", tags=["validation"])
    app.include_router(experiment.router, prefix="/api", tags=["experiment"])
    app.include_router(admet.router,      prefix="/api", tags=["admet"])
    app.include_router(static.router,     prefix="/api", tags=["static"])
    app.include_router(settings.router,   prefix="/api", tags=["settings"])
    app.include_router(rcsb.router,         prefix="/api", tags=["rcsb"])
    app.include_router(selectivity.router, prefix="/api", tags=["selectivity"])
    app.include_router(ui_integrations.router, prefix="/api", tags=["ui-integrations"])

    return app


# uvicorn pipeline_local.backend.main:app 으로 직접 임포트할 때 사용
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pipeline_local.backend.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        reload_dirs=["pipeline_local"],
    )
