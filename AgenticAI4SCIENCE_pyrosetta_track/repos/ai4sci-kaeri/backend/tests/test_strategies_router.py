from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.routers import strategies


def test_strategy_runner_mock_job_smoke() -> None:
    app = FastAPI()
    app.include_router(strategies.router, prefix="/api")
    client = TestClient(app, raise_server_exceptions=True)

    listed = client.get("/api/strategies")
    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()} == {"blosum", "esm_scan", "proteinmpnn", "dual_b1_b2"}

    options = client.get("/api/strategies/proteinmpnn/options")
    assert options.status_code == 200
    assert {item["id"] for item in options.json()["modes"]} == {"peptide_only", "receptor_context"}

    started = client.post(
        "/api/strategies/run",
        json={
            "strategy": "proteinmpnn",
            "mode": "peptide_only",
            "max_variants": 3,
            "num_seq_per_target": 2,
            "config": {"temperature": 0.1},
        },
    )
    assert started.status_code == 200
    job_id = started.json()["job_id"]

    status = client.get(f"/api/strategies/runs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    assert status.json()["progress"] == 100

    variants = client.get(f"/api/strategies/runs/{job_id}/variants")
    assert variants.status_code == 200
    variant_ids = [item["id"] for item in variants.json()]
    assert len(variant_ids) == 3

    selection = client.post(
        f"/api/strategies/runs/{job_id}/select",
        json={
            "selected_variant_ids": [variant_ids[0], variant_ids[1]],
            "rejected_variant_ids": [variant_ids[2]],
        },
    )
    assert selection.status_code == 200
    assert selection.json()["selected_variant_ids"] == [variant_ids[0], variant_ids[1]]

    selected = client.get(f"/api/strategies/runs/{job_id}/selected")
    assert selected.status_code == 200
    assert [item["id"] for item in selected.json()] == [variant_ids[0], variant_ids[1]]
