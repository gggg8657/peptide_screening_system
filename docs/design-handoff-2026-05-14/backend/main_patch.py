"""
패치 가이드 — 기존 main.py 에 추가할 코드 스니펫.

기존 파일 예시 위치:
  AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/main.py
  pipeline_local/backend/main.py

아래 import + include_router 호출만 추가하면 됨.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. import 추가 (다른 라우터 import 옆에)

from .routers import (
    agents as agents_router,
    cand03_variants as cand03_variants_router,
    runs as runs_router,
    benchmark as benchmark_router,
    wetlab as wetlab_router,
    pipelines as pipelines_router,
)


# ─────────────────────────────────────────────────────────────────────────────
# 2. app 생성 직후 (또는 다른 include_router 옆에)
#
# from fastapi import FastAPI
# app = FastAPI(...)
# # ... 기존 router 마운트 ...

app.include_router(agents_router.router,          prefix="/api/agents",          tags=["agents"])
app.include_router(cand03_variants_router.router, prefix="/api/cand03_variants", tags=["cand03"])
app.include_router(runs_router.router,            prefix="/api/runs",            tags=["runs"])
app.include_router(benchmark_router.router,       prefix="/api/benchmark",       tags=["benchmark"])
app.include_router(wetlab_router.router,          prefix="/api/wetlab",          tags=["wetlab"])
app.include_router(pipelines_router.router,       prefix="/api/pipelines",       tags=["pipelines"])


# ─────────────────────────────────────────────────────────────────────────────
# 3. CORS — Vite dev (5173) 에서 호출 시 (이미 설정돼 있으면 skip)
#
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# ─────────────────────────────────────────────────────────────────────────────
# 4. 실행 확인
#
# $ conda activate bio-tools
# $ uvicorn backend.main:app --host 127.0.0.1 --port 8787 --reload
# $ curl http://127.0.0.1:8787/api/cand03_variants/list | jq
# $ curl http://127.0.0.1:8787/api/pipelines/B | jq
# $ curl http://127.0.0.1:8787/api/benchmark/results?phase=V2 | jq
