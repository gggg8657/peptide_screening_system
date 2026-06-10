"""Regression tests for P0 migration router additions."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[2]
AI4SCI_ROOT = REPO_ROOT / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"
if str(AI4SCI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI4SCI_ROOT))

from backend.main import create_app
from backend.routers import agents as agents_router
from backend.routers import cand03_variants as cand03_router


def test_agents_router_prefers_runs_local_ssot() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        run_id = "local_20260514_0240_iter01"
        primary = tmp_root / "runs_local" / run_id / "experiment_log.jsonl"
        compat = tmp_root / "runs_local" / run_id / "silo_b" / "experiment_log.jsonl"
        legacy = tmp_root / "runs" / "pyrosetta_flow" / "experiment_log.jsonl"

        primary.parent.mkdir(parents=True, exist_ok=True)
        compat.parent.mkdir(parents=True, exist_ok=True)
        legacy.parent.mkdir(parents=True, exist_ok=True)

        primary.write_text(
            json.dumps(
                {
                    "ts": "2026-05-14T02:40:01+00:00",
                    "agent": "critic",
                    "level": "info",
                    "text": "primary path selected",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        compat.write_text(
            json.dumps(
                {
                    "ts": "2026-05-14T02:40:02+00:00",
                    "agent": "critic",
                    "level": "warning",
                    "text": "compat path should not be used",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        legacy.write_text(
            json.dumps(
                {
                    "ts": "2026-05-14T02:40:03+00:00",
                    "agent": "critic",
                    "level": "error",
                    "text": "legacy path should not be used",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        original_workspace_root = agents_router._workspace_root
        original_exp_log = agents_router.EXP_LOG
        try:
            agents_router._workspace_root = lambda: tmp_root
            agents_router.EXP_LOG = legacy

            payload = asyncio.run(agents_router.get_agent_log(run_id))
            assert len(payload.agents) == 6
            assert payload.entries[0].text == "primary path selected"
            assert payload.entries[0].level == "info"
        finally:
            agents_router._workspace_root = original_workspace_root
            agents_router.EXP_LOG = original_exp_log


def test_cand03_variants_list_schema() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        variants_path = tmp_root / "runs_local" / "cand03_variants" / "cand03_variants.json"
        variants_path.parent.mkdir(parents=True, exist_ok=True)
        variants_path.write_text(
            json.dumps(
                {
                    "baseline": "cand03",
                    "variants": [
                        {
                            "id": "cand03",
                            "name": "cand03 (A1I)",
                            "seq": "AICKNFFWKTFTSC",
                            "modifications": ["cyclization"],
                            "hl_score": 12.34,
                            "chymotrypsin_sites": 4,
                            "trypsin_sites": 2,
                            "nep_sites": 5,
                            "priority": "baseline",
                            "rationale": "mock payload",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

        original_workspace_root = cand03_router._workspace_root
        try:
            cand03_router._workspace_root = lambda: tmp_root
            payload = cand03_router.list_variants()
            dumped = payload.model_dump()
            assert dumped["baseline"] == "cand03"
            assert len(dumped["variants"]) == 1
            variant = dumped["variants"][0]
            assert set(variant.keys()) == {
                "id",
                "name",
                "seq",
                "modifications",
                "hl_score",
                "chymotrypsin_sites",
                "trypsin_sites",
                "nep_sites",
                "priority",
                "rationale",
            }
            assert variant["id"] == "cand03"
            assert variant["hl_score"] == 12.34
        finally:
            cand03_router._workspace_root = original_workspace_root


def test_main_mounts_migration_routers() -> None:
    app = create_app()
    routes = {(route.path, tuple(sorted(route.methods or []))) for route in app.routes}

    assert ("/api/agents/{run_id}/log", ("GET",)) in routes
    assert ("/api/agents/{run_id}/stream", ("GET",)) in routes
    assert ("/api/cand03_variants/list", ("GET",)) in routes
