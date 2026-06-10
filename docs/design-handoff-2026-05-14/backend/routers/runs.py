"""
새 파이프라인 실행 시작 + 예상 통과율 라우터.

마운트:
  app.include_router(runs.router, prefix="/api/runs", tags=["runs"])

기존 status 라우터와 충돌하지 않도록 prefix 주의.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..schemas.dashboard import (  # type: ignore
    RunStartRequest, RunStartResponse,
    PredictedPassRate, PredictedPassRatesResponse,
)

router = APIRouter()
KST = timezone(timedelta(hours=9))


def _now_kst() -> datetime:
    return datetime.now(KST)


def _build_run_id(name: str | None = None) -> str:
    ts = _now_kst().strftime("%Y%m%d_%H%M")
    return name or f"local_{ts}_iter01"


def _runs_root() -> Path:
    return Path(__file__).resolve().parents[3] / "runs_local"


@router.post("/start", response_model=RunStartResponse)
async def start_run(req: RunStartRequest, bg: BackgroundTasks) -> RunStartResponse:
    """새 파이프라인 실행 시작 — 비동기. 실제 subprocess 호출은 TODO."""
    run_id = _build_run_id(req.name)
    started = _now_kst()

    # 1. config 작성
    run_dir = _runs_root() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = run_dir / "00_config" / "pipeline_config_local.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(_render_yaml(req), encoding="utf-8")

    # 2. ETA 산정 (대략)
    eta = _estimate_eta(req)

    # 3. subprocess 실행 — async background
    bg.add_task(_run_pipeline_subprocess, run_id, req)

    return RunStartResponse(
        run_id=run_id,
        started_at=started,
        estimated_eta_minutes=eta,
        monitor_url=f"/runs/{run_id}",
    )


def _render_yaml(req: RunStartRequest) -> str:
    """RunStartRequest → pipeline_config_local.yaml. 간략 dump."""
    import yaml
    payload = {
        "mode": "local",
        "iteration": {
            "n_backbone": req.n_backbone,
            "k_seq_per_backbone": req.k_seq_per_backbone,
            "top_m_rosetta": req.top_m_rosetta,
            "max_iterations": req.iterations,
        },
        "silo": req.silo,
        "llm_model": req.llm_model,
        "seed": req.seed,
        "mutation_strategy": req.mutation_strategy,
        "off_target_receptors": req.off_targets,
        "boltz_cross": {"enabled": req.boltz_cross_enabled},
        "gates": req.gates.model_dump() if req.gates else None,
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def _estimate_eta(req: RunStartRequest) -> int:
    """ETA (분). iter02 데이터 기반 회귀 — 단순 휴리스틱."""
    per_iter = 28 if req.silo == "B" else 32 if req.silo == "A" else 47
    bc = 8 if req.boltz_cross_enabled else 0
    return per_iter * req.iterations + bc * req.iterations


def _run_pipeline_subprocess(run_id: str, req: RunStartRequest) -> None:
    """subprocess 호출 — bio-tools env 에서 pipeline_local 모듈 실행."""
    # TODO: conda run 또는 직접 모듈 호출
    cmd = [
        "conda", "run", "-n", "bio-tools",
        "python", "-m", "pipeline_local.run_pipeline_local",
        "--run-id", run_id,
        "--iterations", str(req.iterations),
        "--silo", req.silo,
        "--llm-model", req.llm_model,
    ]
    log_path = _runs_root() / run_id / "stdout.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as logf:
        subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT)


# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{run_id}/predicted_pass_rates", response_model=PredictedPassRatesResponse)
def predicted_pass_rates(run_id: str) -> PredictedPassRatesResponse:
    """이전 N개 실행 기반 게이트 예상 통과율. 단순 회귀 또는 lookup."""
    # TODO: runs/pyrosetta_flow/archives/ 누적 통계 활용
    return PredictedPassRatesResponse(
        based_on="iter02 + 4 historical runs",
        predicted=[
            PredictedPassRate(gate_id="G1",  name="pLDDT",              rate=0.91),
            PredictedPassRate(gate_id="G2",  name="Docking",            rate=0.22),
            PredictedPassRate(gate_id="G3",  name="Selectivity",        rate=0.50),
            PredictedPassRate(gate_id="G3b", name="Boltz iPTM margin",  rate=0.12, warn=True),
            PredictedPassRate(gate_id="G4",  name="Rosetta ddG",        rate=1.00),
            PredictedPassRate(gate_id="G5",  name="Stability",          rate=1.00),
        ],
    )
