"""Regression tests for migration P1 benchmark and pipelines routers."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]
APP_ROOT = Path(__file__).resolve().parents[2]

for path in (REPO_ROOT, APP_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from backend.main import create_app  # noqa: E402
from backend.routers.benchmark import benchmark_results  # noqa: E402
from backend.routers.pipelines import get_pipeline  # noqa: E402


app = create_app()


def test_benchmark_results_v2_schema() -> None:
    sample_runs = [
        {
            "model": "qwen3_32b",
            "flow": "v2_sequential",
            "elapsed_s": 300,
            "ses": {"hit_rate": 0.5, "n_total": 8, "n_hits": 2},
        },
        {
            "model": "qwen3_32b",
            "flow": "v2_sequential",
            "elapsed_s": 420,
            "ses": {"hit_rate": 0.75, "n_total": 10, "n_hits": 3},
        },
    ]
    with patch("backend.routers.benchmark.load_phase_results", side_effect=[sample_runs, []]):
        payload = benchmark_results(phase="V2").model_dump()

    assert payload["phase"] == "V2"
    assert payload["total_runs"] == 2
    assert payload["llms"][0]["id"] == "qwen3-32b"
    assert payload["flows"][0]["id"] == "sequential"
    assert payload["matrix"]["qwen3-32b"]["sequential"]["candidates"] == 9


def test_pipeline_a_contains_expected_stages() -> None:
    payload = get_pipeline("A", run_id=None).model_dump(by_alias=True)
    stage_ids = [stage["id"] for stage in payload["stages"]]
    assert stage_ids == ["01", "02", "03", "04", "05", "05b", "05c", "06", "07", "08"]
    assert payload["stages"][1]["env"] == "rfdiffusion"
    assert payload["stages"][1]["description"]


def test_pipeline_b_contains_step03b() -> None:
    payload = get_pipeline("B", run_id=None).model_dump(by_alias=True)
    stage_ids = [stage["id"] for stage in payload["stages"]]
    assert "03b" in stage_ids
    mutation_stage = next(stage for stage in payload["stages"] if stage["id"] == "03b")
    assert mutation_stage["name"] == "Mutation"
    assert mutation_stage["env"] == "vllm-server"


def test_routes_are_mounted() -> None:
    route_paths = {route.path for route in app.routes}
    assert "/api/benchmark/results" in route_paths
    assert "/api/pipelines/{silo}" in route_paths
