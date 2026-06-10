"""
FastAPI Application Factory
=============================
Entry point for the pipeline monitoring API.

Usage:
    uvicorn backend.main:app --host 0.0.0.0 --port 8787 --reload

Or programmatically:
    from backend.main import create_app
    app = create_app()
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers import (
    admet,
    agents,
    analysis,
    benchmark,
    binding_pocket,
    cand03_variants,
    cluster,
    experiment,
    flexpepdock,
    pipelines,
    rcsb,
    runs,
    selectivity,
    settings,
    silo_a as silo_a_router,
    stability,
    strategies,
    static,
    status,
    validation,
    wetlab,
)
from backend.state import PORT


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Router prefix structure is designed for future multi-pipeline support:
        /api/          — current pyrosetta pipeline (default)
        /api/v1/silo-a/  — future 3-ARM virtual screening pipeline
        /api/v1/silo-b/  — future SST-14 mutation simulation pipeline

    To add a new pipeline, create a new router module and include it
    with the appropriate prefix, e.g.:
        app.include_router(silo_a_router, prefix="/api/v1/silo-a")
    """
    app = FastAPI(
        title="AI4Sci Pipeline Monitor",
        description="Pipeline monitoring API for SSTR2 radiopharmaceutical candidate screening",
        version="2.0.0",
    )

    # CORS — replaces manual header injection in legacy server
    # PUT/DELETE 허용: binding_pocket UI 편집 지원
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8787"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    # Standard error response: {"error": str, "detail": str, "status_code": int}
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "detail": "Internal server error",
                "status_code": 500,
            },
        )

    from fastapi.exceptions import HTTPException as FastAPIHTTPException

    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTPException",
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
        )

    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "detail": str(exc),
                "status_code": 422,
            },
        )

    # All current routers under /api prefix
    # Extension point: future pipeline routers can be added here with
    # versioned prefixes (e.g. /api/v1/pyrosetta, /api/v1/silo-a)
    app.include_router(status.router,           prefix="/api", tags=["status"])
    app.include_router(analysis.router,         prefix="/api", tags=["analysis"])
    app.include_router(validation.router,       prefix="/api", tags=["validation"])
    app.include_router(experiment.router,       prefix="/api", tags=["experiment"])
    app.include_router(admet.router,            prefix="/api", tags=["admet"])
    app.include_router(static.router,           prefix="/api", tags=["static"])
    app.include_router(settings.router,         prefix="/api", tags=["settings"])
    app.include_router(rcsb.router,             prefix="/api", tags=["rcsb"])
    app.include_router(cluster.router,          prefix="/api", tags=["cluster"])
    app.include_router(selectivity.router,      prefix="/api", tags=["selectivity"])
    app.include_router(stability.router,        prefix="/api", tags=["stability"])
    app.include_router(agents.router,           prefix="/api", tags=["agents"])
    app.include_router(runs.router,             prefix="/api/runs", tags=["runs"])
    app.include_router(cand03_variants.router,  prefix="/api", tags=["cand03_variants"])
    app.include_router(benchmark.router,        prefix="/api/benchmark", tags=["benchmark"])
    app.include_router(pipelines.router,        prefix="/api/pipelines", tags=["pipelines"])
    app.include_router(wetlab.router,           prefix="/api/wetlab", tags=["wetlab"])
    app.include_router(flexpepdock.router,      prefix="/api", tags=["flexpepdock"])
    app.include_router(binding_pocket.router,   prefix="/api", tags=["binding_pocket"])
    app.include_router(strategies.router,       prefix="/api", tags=["strategies"])
    app.include_router(silo_a_router.router,    prefix="/api/v1/silo-a", tags=["silo_a"])

    return app


# Module-level app for `uvicorn backend.main:app`
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=PORT, reload=True)
