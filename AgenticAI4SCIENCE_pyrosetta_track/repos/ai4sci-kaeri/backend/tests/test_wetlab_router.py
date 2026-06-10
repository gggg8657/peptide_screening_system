"""Regression tests for PRST wetlab order integration."""
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

from backend.routers import wetlab  # noqa: E402


def test_orders_include_prst_synthesis_requests() -> None:
    payload = wetlab.list_orders()
    orders = {order["candidate_id"]: order for order in payload["orders"]}

    assert {"PRST-001", "PRST-002", "PRST-003", "PRST-004"}.issubset(orders)
    assert "cand03" in orders


def test_prst_orders_have_valid_list_schema() -> None:
    payload = wetlab.list_orders()
    prst_orders = [order for order in payload["orders"] if order["candidate_id"].startswith("PRST-")]

    assert len(prst_orders) == 4
    for order in prst_orders:
        assert set(("id", "candidate_id", "sequence", "predicted_ddg", "admet_tox", "state", "created_at")).issubset(order)
        assert order["id"].startswith("WO-2026-PRST-")
        assert order["sequence"]
        assert isinstance(order["predicted_ddg"], float)
        assert isinstance(order["admet_tox"], float)
        assert order["state"] == wetlab.PRST_SYNTHESIS_STATE
        assert order["created_at"]


def test_prst_orders_merge_with_legacy_store() -> None:
    legacy_orders = [wetlab._build_cand03_order()]

    with patch("backend.routers.wetlab._orders_store") as store_mock, patch("backend.routers.wetlab._save_orders") as save_mock:
        store_mock.return_value.exists.return_value = True
        store_mock.return_value.open.return_value.__enter__.return_value.read.return_value = ""
        with patch("json.load", return_value=legacy_orders):
            orders = wetlab._load_orders()

    assert [order["candidate_id"] for order in orders].count("cand03") == 1
    assert {order["candidate_id"] for order in orders if order["candidate_id"].startswith("PRST-")} == {
        "PRST-001",
        "PRST-002",
        "PRST-003",
        "PRST-004",
    }
    save_mock.assert_called_once()
