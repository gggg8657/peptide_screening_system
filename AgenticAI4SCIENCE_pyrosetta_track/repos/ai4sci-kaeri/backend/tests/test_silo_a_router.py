from __future__ import annotations

import re
import sys
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.routers import silo_a


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(silo_a.router, prefix="/api/v1/silo-a")
    return TestClient(app, raise_server_exceptions=True)


def test_health_returns_phase_1_info(monkeypatch) -> None:
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.setattr(silo_a, "_discover_conda_env_names", lambda: set())

    response = _client().get("/api/v1/silo-a/health")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "silo_a"
    assert data["phase"] == "phase_1"
    assert data["status"] == "ok"
    assert data["dry_run"] is True
    assert data["nim"]["mode"] == "dry_run"


def test_run_returns_job_id_with_uuid(monkeypatch) -> None:
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "test-key")

    response = _client().post(
        "/api/v1/silo-a/run",
        json={"sequences": ["AGCKNFFWKTFTSC"], "use_nim": True, "arms": ["mpnn"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert UUID(data["job_id"])
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        data["job_id"],
    )
    assert data["status"] == "queued"


def test_run_dry_run_when_no_nim_key(monkeypatch) -> None:
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)

    response = _client().post(
        "/api/v1/silo-a/run",
        json={"sequences": ["AGCKNFFWKTFTSC"], "use_nim": True, "arms": ["mpnn"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True
    assert data["use_nim"] is False


def test_status_stub_response() -> None:
    response = _client().get("/api/v1/silo-a/status/job-123")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-123",
        "status": "stub",
        "phase": "phase_1",
        "message": "Phase 1 status stub; persistent job tracking is deferred to Phase 2.",
    }


def test_results_stub_response() -> None:
    response = _client().get("/api/v1/silo-a/results/job-123")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-123",
        "status": "stub",
        "phase": "phase_1",
        "results": [],
        "message": "Phase 1 results stub; model outputs are deferred to Phase 2.",
    }


def test_health_reports_conda_envs(monkeypatch) -> None:
    monkeypatch.setattr(
        silo_a,
        "_discover_conda_env_names",
        lambda: {"proteinmpnn", "esmfold"},
    )

    response = _client().get("/api/v1/silo-a/health")

    assert response.status_code == 200
    envs = response.json()["conda_envs"]
    assert set(envs) == {"proteinmpnn", "rfdiffusion", "esmfold", "diffpepbuilder"}
    assert envs["proteinmpnn"]["available"] is True
    assert envs["esmfold"]["available"] is True
    assert envs["rfdiffusion"]["available"] is False
    assert envs["diffpepbuilder"]["available"] is False
