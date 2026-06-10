"""Silo A local router Phase 1.

Phase 1 intentionally exposes dry-run orchestration and health probes only.
Real ProteinMPNN, RFdiffusion, ESMFold, and DiffPepBuilder calls are reserved
for the Phase 2 worker integration.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

REQUIRED_CONDA_ENVS = ("proteinmpnn", "rfdiffusion", "esmfold", "diffpepbuilder")


class SiloARunRequest(BaseModel):
    sequences: list[str] = Field(default_factory=list)
    use_nim: bool = True
    arms: list[str] = Field(default_factory=list)


class SiloARunResponse(BaseModel):
    job_id: str
    status: str
    phase: str
    dry_run: bool
    use_nim: bool
    message: str


class SiloAStatusResponse(BaseModel):
    job_id: str
    status: str
    phase: str
    message: str


class SiloAResultsResponse(BaseModel):
    job_id: str
    status: str
    phase: str
    results: list[dict[str, Any]]
    message: str


class SiloAHealthResponse(BaseModel):
    service: str
    phase: str
    status: str
    dry_run: bool
    nim: dict[str, Any]
    conda_envs: dict[str, dict[str, Any]]
    checked_at: datetime


def _has_nim_api_key() -> bool:
    return bool(os.getenv("NVIDIA_NIM_API_KEY"))


def _nim_dry_run_enabled(requested_use_nim: bool = True) -> bool:
    return requested_use_nim and not _has_nim_api_key()


def _discover_conda_env_names() -> set[str]:
    conda = shutil.which("conda")
    if conda is None:
        return set()

    try:
        completed = subprocess.run(
            [conda, "env", "list", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return set()

    if completed.returncode != 0:
        return set()

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return set()

    envs = payload.get("envs", [])
    if not isinstance(envs, list):
        return set()

    names: set[str] = set()
    for env_path in envs:
        if isinstance(env_path, str) and env_path:
            names.add(os.path.basename(env_path.rstrip(os.sep)))
    return names


def _conda_env_status() -> dict[str, dict[str, Any]]:
    available = _discover_conda_env_names()
    return {
        env: {
            "available": env in available,
            "name": env,
        }
        for env in REQUIRED_CONDA_ENVS
    }


@router.post("/run", response_model=SiloARunResponse)
def run_silo_a(request: SiloARunRequest) -> SiloARunResponse:
    dry_run = _nim_dry_run_enabled(request.use_nim)
    return SiloARunResponse(
        job_id=str(uuid4()),
        status="queued",
        phase="phase_1",
        dry_run=dry_run,
        use_nim=request.use_nim and _has_nim_api_key(),
        message="Silo A Phase 1 dry-run job accepted; inference is deferred to Phase 2.",
    )


@router.get("/status/{job_id}", response_model=SiloAStatusResponse)
def get_silo_a_status(job_id: str) -> SiloAStatusResponse:
    return SiloAStatusResponse(
        job_id=job_id,
        status="stub",
        phase="phase_1",
        message="Phase 1 status stub; persistent job tracking is deferred to Phase 2.",
    )


@router.get("/results/{job_id}", response_model=SiloAResultsResponse)
def get_silo_a_results(job_id: str) -> SiloAResultsResponse:
    return SiloAResultsResponse(
        job_id=job_id,
        status="stub",
        phase="phase_1",
        results=[],
        message="Phase 1 results stub; model outputs are deferred to Phase 2.",
    )


@router.get("/health", response_model=SiloAHealthResponse)
def get_silo_a_health() -> SiloAHealthResponse:
    nim_key_present = _has_nim_api_key()
    conda_envs = _conda_env_status()
    return SiloAHealthResponse(
        service="silo_a",
        phase="phase_1",
        status="ok",
        dry_run=not nim_key_present,
        nim={
            "api_key_present": nim_key_present,
            "mode": "configured" if nim_key_present else "dry_run",
        },
        conda_envs=conda_envs,
        checked_at=datetime.now(timezone.utc),
    )
