"""Regression tests for migration P2 runs and agents routers."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[5]
APP_ROOT = Path(__file__).resolve().parents[2]

for path in (REPO_ROOT, APP_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from backend.main import create_app  # noqa: E402
from backend.routers import agents as agents_router  # noqa: E402
from backend.routers import runs as runs_router  # noqa: E402


def test_predicted_pass_rates_uses_archive_statistics() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        gate_path = tmp_root / "pipeline_local" / "config" / "gate_thresholds.yaml"
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(
            "\n".join(
                [
                    "gates_enabled:",
                    "  plddt: true",
                    "  docking: false",
                    "  rosetta: true",
                    "  selectivity: true",
                    "  stability_prescreen: false",
                    "rosetta_ddg_max: -1.0",
                ]
            ),
            encoding="utf-8",
        )

        history_root = tmp_root / "runs_local" / "silo_b_hist_01" / "local_20260514_0100_iter01"
        rosetta_path = history_root / "06_rosetta" / "energy_table.json"
        boltz_path = history_root / "05c_boltz_cross" / "boltz_cross_validation.json"
        rosetta_path.parent.mkdir(parents=True, exist_ok=True)
        boltz_path.parent.mkdir(parents=True, exist_ok=True)
        rosetta_path.write_text(
            json.dumps(
                {
                    "results": [
                        {"ddg": -2.0},
                        {"ddg": -0.5},
                        {"ddg": -1.5},
                    ]
                }
            ),
            encoding="utf-8",
        )
        boltz_path.write_text(
            json.dumps(
                {
                    "results": [
                        {"selectivity_margin": 0.20},
                        {"selectivity_margin": -0.10},
                        {"selectivity_margin": 0.05},
                    ]
                }
            ),
            encoding="utf-8",
        )

        current_root = tmp_root / "runs_local" / "silo_b_hist_02" / "local_target_iter01"
        (current_root / "06_rosetta").mkdir(parents=True, exist_ok=True)
        (current_root / "06_rosetta" / "energy_table.json").write_text(
            json.dumps({"results": [{"ddg": 100.0}]}),
            encoding="utf-8",
        )

        with patch.object(runs_router, "_repo_root", return_value=tmp_root):
            payload = runs_router.predicted_pass_rates("local_target_iter01").model_dump()

        predicted = {item["gate_id"]: item for item in payload["predicted"]}
        assert payload["based_on"].startswith("gate_thresholds.yaml + ")
        assert predicted["plddt"]["rate"] == 0.5
        assert predicted["plddt"]["warn"] is True
        assert predicted["rosetta"]["rate"] == 2 / 3
        assert predicted["rosetta"]["warn"] is False
        assert predicted["selectivity"]["rate"] == 2 / 3
        assert predicted["selectivity"]["warn"] is False


def test_runs_start_rejects_duplicate_active_run() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        runs_root = tmp_root / "runs_local"
        runs_root.mkdir(parents=True, exist_ok=True)
        (runs_root / runs_router.LOCKFILE_NAME).write_text(
            json.dumps(
                {
                    "run_id": "local_existing_iter01",
                    "pid": os.getpid(),
                    "status": "running",
                }
            ),
            encoding="utf-8",
        )

        app = create_app()
        with TestClient(app) as client, patch.object(runs_router, "_repo_root", return_value=tmp_root):
            response = client.post(
                "/api/runs/start",
                json={
                    "name": "local_new_iter01",
                    "silo": "B",
                    "iterations": 2,
                },
            )

        assert response.status_code == 409
        assert response.json()["detail"] == "run already active: local_existing_iter01"


def test_agents_stream_emits_sse_events_from_file_tail() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        run_id = "local_20260514_0900_iter01"
        log_path = tmp_root / "runs_local" / run_id / "experiment_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("", encoding="utf-8")

        class DummyRequest:
            disconnected = False

            async def is_disconnected(self) -> bool:
                return self.disconnected

        async def exercise_stream() -> tuple[str, str]:
            request = DummyRequest()

            def append_log_line() -> None:
                time.sleep(0.5)
                with log_path.open("a", encoding="utf-8") as handle:
                    handle.write(
                        json.dumps(
                            {
                                "ts": "2026-05-14T09:00:01+00:00",
                                "agent": "critic",
                                "level": "info",
                                "text": "tail event delivered",
                            }
                        )
                        + "\n"
                    )

            writer = threading.Thread(target=append_log_line, daemon=True)
            writer.start()

            with patch.object(agents_router, "_workspace_root", return_value=tmp_root):
                response = await agents_router.stream_agent_log(run_id, request)
                body_iter = response.body_iterator
                retry_chunk = await asyncio.wait_for(anext(body_iter), timeout=1)
                event_chunk = await asyncio.wait_for(anext(body_iter), timeout=3)
                request.disconnected = True
                await body_iter.aclose()

            writer.join(timeout=2)
            return retry_chunk.decode("utf-8"), event_chunk.decode("utf-8")

        retry_chunk, event_chunk = asyncio.run(exercise_stream())
        data_line = next(line for line in event_chunk.splitlines() if line.startswith("data: "))
        payload = json.loads(data_line.removeprefix("data: "))

        assert retry_chunk == "retry: 3000\n\n"
        assert "event: agent" in event_chunk
        assert payload["agent"] == "critic"
        assert payload["text"] == "tail event delivered"
