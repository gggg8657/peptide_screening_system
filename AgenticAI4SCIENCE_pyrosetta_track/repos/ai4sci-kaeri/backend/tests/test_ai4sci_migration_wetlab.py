"""Regression tests for wetlab order migration router."""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]
APP_ROOT = Path(__file__).resolve().parents[2]

for path in (REPO_ROOT, APP_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

if "aiofiles" not in sys.modules:
    aiofiles_stub = types.ModuleType("aiofiles")
    aiofiles_stub.open = None  # pragma: no cover - shim for import-time dependency only
    sys.modules["aiofiles"] = aiofiles_stub

from backend.main import create_app  # noqa: E402
from backend.routers import wetlab  # noqa: E402

app = create_app()


def test_wetlab_routes_are_mounted() -> None:
    route_paths = {route.path for route in app.routes}
    assert "/api/wetlab/orders" in route_paths
    assert "/api/wetlab/orders/{order_id}" in route_paths
    assert "/api/wetlab/orders/{order_id}/transition" in route_paths


def test_list_orders_seeds_default_when_store_missing() -> None:
    with patch("backend.routers.wetlab._orders_store") as store_mock:
        store_mock.return_value = Path("/tmp/nonexistent-wetlab-orders.json")
        payload = wetlab.list_orders().model_dump()

    assert payload["orders"][0]["id"] == "WO-2026-005"
    assert payload["orders"][0]["stage"] == "approved"


def test_transition_advances_one_step() -> None:
    orders = [wetlab._build_cand03_order()]
    orders[0]["stage"] = "draft"

    with patch("backend.routers.wetlab._load_orders", return_value=orders), patch("backend.routers.wetlab._save_orders") as save_mock:
        payload = wetlab.transition_order("WO-2026-005", wetlab.WetlabTransitionRequest(to_stage="submitted")).model_dump()

    assert payload["stage"] == "submitted"
    save_mock.assert_called_once()


def test_transition_rejects_jumps() -> None:
    orders = [wetlab._build_cand03_order()]
    orders[0]["stage"] = "draft"

    with patch("backend.routers.wetlab._load_orders", return_value=orders):
        try:
            wetlab.transition_order("WO-2026-005", wetlab.WetlabTransitionRequest(to_stage="approved"))
        except Exception as exc:  # HTTPException
            assert "cannot jump" in str(exc.detail)
        else:
            raise AssertionError("expected transition jump to fail")
