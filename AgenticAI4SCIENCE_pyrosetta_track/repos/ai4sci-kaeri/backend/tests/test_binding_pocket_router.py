"""
backend/tests/test_binding_pocket_router.py
============================================
Binding Pocket CRUD 엔드포인트 단위 테스트.

테스트 격리:
  - monkeypatch로 DATA_DIR 를 tmp_path로 교체
  - 실제 data/ 디렉토리 파일 접근 없음
  - extract 엔드포인트: extract_pocket_center 모듈 mock 처리

커버리지 항목 (≥6):
  1. GET 200 — 존재하는 포켓 정상 조회
  2. GET 404 — 설정 파일 없음
  3. GET 400 — 알 수 없는 수용체
  4. PUT 200 — 유효한 설정 저장 + box_size 자동 계산
  5. PUT 400 — receptor 불일치 (URL vs body)
  6. PUT 422 — radius_angstrom 범위 초과 (validation error)
  7. PUT 200 — _default.json 자동 백업 생성 확인
  8. DELETE 200 — _default.json 복원 후 백업 파일 삭제 확인
  9. DELETE 200 — 백업 없을 때 파일 삭제 (no-restore)
 10. DELETE 404 — 설정 파일 없음
 11. POST /extract 404 — PDB 파일 없음
 12. POST /extract 200 — extract_pocket_center mock 호출 + 저장 확인
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch, MagicMock

import pytest

# REPO_ROOT를 sys.path에 추가 (backend 패키지 임포트를 위해)
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# 샘플 JSON (실제 binding_pocket_SSTR2.json 구조 기반)
# ---------------------------------------------------------------------------

SAMPLE_SSTR2_POCKET: Dict[str, Any] = {
    "receptor": "SSTR2_7XNA",
    "chain": "A",
    "residues": [205, 208, 209, 212, 272, 273, 276, 279],
    "center_x": -5.595,
    "center_y": -28.626,
    "center_z": 52.21,
    "radius": 13.035,
    "box_size": 26.1,
    "source": "original",
    "gnina_config": {
        "center_x": -5.595,
        "center_y": -28.626,
        "center_z": 52.21,
        "size_x": 26.1,
        "size_y": 26.1,
        "size_z": 26.1,
    },
    "notes": "TM5/TM6 잔기 기반 포켓.",
}

VALID_PUT_BODY: Dict[str, Any] = {
    "receptor": "sstr2",
    "center_x": -5.0,
    "center_y": -28.0,
    "center_z": 52.0,
    "radius_angstrom": 12.0,
    "residue_ids": [208, 209, 272, 273, 276],
    "source": "user_override",
}

MOCK_EXTRACT_RESULT: Dict[str, Any] = {
    "center_x": -5.1,
    "center_y": -28.1,
    "center_z": 52.1,
    "radius_angstrom": 11.5,
    "residue_ids": [208, 209, 272],
    "source_pdb": "/data/SSTR2_7XNA.pdb",
    "box_size": {"size_x": 30.0, "size_y": 30.0, "size_z": 30.0},
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_data_dir(tmp_path: Path) -> Path:
    """격리된 임시 data 디렉토리 반환."""
    d = tmp_path / "somatostatin_receptor"
    d.mkdir(parents=True)
    return d


@pytest.fixture()
def app(tmp_data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    """binding_pocket 라우터만 포함한 테스트 앱 (DATA_DIR 격리)."""
    import backend.routers.binding_pocket as bp_mod

    monkeypatch.setattr(bp_mod, "DATA_DIR", tmp_data_dir)

    test_app = FastAPI()
    test_app.include_router(bp_mod.router, prefix="/api")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """TestClient 반환."""
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def populated_sstr2(tmp_data_dir: Path) -> Path:
    """binding_pocket_SSTR2.json 이 존재하는 상태 픽스처."""
    path = tmp_data_dir / "binding_pocket_SSTR2.json"
    path.write_text(json.dumps(SAMPLE_SSTR2_POCKET, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# TC01: GET 200 — 정상 조회
# ---------------------------------------------------------------------------

def test_get_pocket_200(client: TestClient, populated_sstr2: Path) -> None:
    """GET /api/binding_pocket/sstr2 → 200, 올바른 JSON 반환."""
    resp = client.get("/api/binding_pocket/sstr2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["receptor"] == "SSTR2_7XNA"
    assert data["center_x"] == pytest.approx(-5.595)


# ---------------------------------------------------------------------------
# TC02: GET 404 — 설정 파일 없음
# ---------------------------------------------------------------------------

def test_get_pocket_404(client: TestClient, tmp_data_dir: Path) -> None:
    """GET /api/binding_pocket/sstr3 → 404 (파일 미존재)."""
    resp = client.get("/api/binding_pocket/sstr3")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TC03: GET 400 — 유효하지 않은 수용체
# ---------------------------------------------------------------------------

def test_get_pocket_400_unknown_receptor(client: TestClient) -> None:
    """GET /api/binding_pocket/sstr9 → 400."""
    resp = client.get("/api/binding_pocket/sstr9")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# TC04: PUT 200 — 설정 저장 + box_size 자동 계산
# ---------------------------------------------------------------------------

def test_put_pocket_200_auto_box_size(
    client: TestClient, tmp_data_dir: Path
) -> None:
    """PUT 유효 payload → 200, box_size 자동 계산 (radius×2 vs 30 중 큰 값)."""
    body = dict(VALID_PUT_BODY)
    # box_size 미제공 → 자동 계산 (max(30, 12.0*2) = 30.0)
    body.pop("box_size", None)

    resp = client.put("/api/binding_pocket/sstr2", json=body)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    saved = json.loads(
        (tmp_data_dir / "binding_pocket_SSTR2.json").read_text(encoding="utf-8")
    )
    assert saved["box_size"]["size_x"] == pytest.approx(30.0)
    assert "timestamp" in saved


# ---------------------------------------------------------------------------
# TC05: PUT 400 — receptor 불일치 (URL vs body)
# ---------------------------------------------------------------------------

def test_put_pocket_400_receptor_mismatch(client: TestClient) -> None:
    """PUT URL=sstr2, body.receptor=sstr3 → 400."""
    body = dict(VALID_PUT_BODY)
    body["receptor"] = "sstr3"
    resp = client.put("/api/binding_pocket/sstr2", json=body)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# TC06: PUT 422 — radius_angstrom 범위 초과 (Pydantic validation)
# ---------------------------------------------------------------------------

def test_put_pocket_422_radius_out_of_range(client: TestClient) -> None:
    """PUT radius_angstrom=50 (> 30) → 422 ValidationError."""
    body = dict(VALID_PUT_BODY)
    body["radius_angstrom"] = 50.0
    resp = client.put("/api/binding_pocket/sstr2", json=body)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TC07: PUT — _default.json 자동 백업
# ---------------------------------------------------------------------------

def test_put_creates_default_backup(
    client: TestClient, tmp_data_dir: Path, populated_sstr2: Path
) -> None:
    """PUT 시 기존 원본 → _default.json 백업 생성 확인."""
    default_path = tmp_data_dir / "binding_pocket_SSTR2_default.json"
    assert not default_path.exists()

    resp = client.put("/api/binding_pocket/sstr2", json=VALID_PUT_BODY)
    assert resp.status_code == 200
    assert default_path.exists()

    backup = json.loads(default_path.read_text(encoding="utf-8"))
    assert backup["receptor"] == "SSTR2_7XNA"  # 원본 보존 확인


# ---------------------------------------------------------------------------
# TC08: DELETE 200 — _default.json 복원
# ---------------------------------------------------------------------------

def test_delete_pocket_restores_default(
    client: TestClient, tmp_data_dir: Path
) -> None:
    """DELETE → _default.json 있으면 원본 복원 + 백업 삭제."""
    main_path = tmp_data_dir / "binding_pocket_SSTR2.json"
    default_path = tmp_data_dir / "binding_pocket_SSTR2_default.json"

    # user override 상태 준비
    override = dict(VALID_PUT_BODY, source="user_override", timestamp="2026-01-01T00:00:00+00:00")
    main_path.write_text(json.dumps(override, ensure_ascii=False), encoding="utf-8")
    default_path.write_text(json.dumps(SAMPLE_SSTR2_POCKET, ensure_ascii=False), encoding="utf-8")

    resp = client.delete("/api/binding_pocket/sstr2")
    assert resp.status_code == 200
    result = resp.json()
    assert result["ok"] is True
    assert result["restored"] is True

    # 원본 복원 확인
    restored = json.loads(main_path.read_text(encoding="utf-8"))
    assert restored["receptor"] == "SSTR2_7XNA"

    # 백업 파일 삭제 확인
    assert not default_path.exists()


# ---------------------------------------------------------------------------
# TC09: DELETE 200 — 백업 없이 파일 삭제
# ---------------------------------------------------------------------------

def test_delete_pocket_no_backup(
    client: TestClient, tmp_data_dir: Path, populated_sstr2: Path
) -> None:
    """DELETE → _default.json 없을 때 파일 삭제 + restored=False."""
    resp = client.delete("/api/binding_pocket/sstr2")
    assert resp.status_code == 200
    result = resp.json()
    assert result["ok"] is True
    assert result["restored"] is False
    assert not (tmp_data_dir / "binding_pocket_SSTR2.json").exists()


# ---------------------------------------------------------------------------
# TC10: DELETE 404 — 설정 파일 없음
# ---------------------------------------------------------------------------

def test_delete_pocket_404(client: TestClient, tmp_data_dir: Path) -> None:
    """DELETE /api/binding_pocket/sstr2 (파일 없음) → 404."""
    resp = client.delete("/api/binding_pocket/sstr2")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TC11: POST /extract 404 — PDB 파일 없음
# ---------------------------------------------------------------------------

def test_extract_pocket_404_no_pdb(client: TestClient, tmp_data_dir: Path) -> None:
    """POST /extract 시 PDB 파일 없으면 → 404."""
    resp = client.post(
        "/api/binding_pocket/sstr2/extract",
        json={"residue_ids": [208, 209, 272]},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TC12: POST /extract 200 — extract_pocket_center mock 정상 호출
# ---------------------------------------------------------------------------

def test_extract_pocket_200_mock(
    client: TestClient, tmp_data_dir: Path
) -> None:
    """POST /extract → extract_pocket_center mock 호출 + JSON 저장 확인."""
    # 가짜 PDB 파일 생성 (내용은 irrelevant, 경로 존재 확인용)
    fake_pdb = tmp_data_dir / "SSTR2_7XNA.pdb"
    fake_pdb.write_text("FAKE PDB CONTENT\n", encoding="utf-8")

    mock_fn = MagicMock(return_value=MOCK_EXTRACT_RESULT)

    with patch(
        "backend.routers.binding_pocket.extract_pocket_center",
        mock_fn,
        create=True,
    ):
        # extract_pocket_center를 직접 임포트하는 lazy import를 mock하기 위해
        # binding_pocket 모듈 내 임포트 경로에 inject
        import backend.routers.binding_pocket as bp_mod

        original_import = bp_mod.__builtins__  # noqa: F841 — 참조 유지용

        with patch.dict(
            "sys.modules",
            {
                "pipeline_local.scripts.extract_binding_pocket": MagicMock(
                    extract_pocket_center=mock_fn
                )
            },
        ):
            resp = client.post(
                "/api/binding_pocket/sstr2/extract",
                json={"residue_ids": [208, 209, 272]},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["center_x"] == pytest.approx(-5.1)
    assert data["source"] == "auto_extract"
    assert "timestamp" in data

    # 저장 파일 확인
    saved_path = tmp_data_dir / "binding_pocket_SSTR2.json"
    assert saved_path.exists()
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved["radius_angstrom"] == pytest.approx(11.5)


# ---------------------------------------------------------------------------
# TC13: PUT 422 — box_size 잘못된 키 (H-2 회귀 방지)
# ---------------------------------------------------------------------------

def test_put_box_size_invalid_key_rejected(client: TestClient) -> None:
    """PUT box_size={'wrong_key': 99} → 422 (size_x/y/z 필수 키 누락)."""
    body = dict(VALID_PUT_BODY)
    body["box_size"] = {"wrong_key": 99}
    resp = client.put("/api/binding_pocket/sstr2", json=body)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TC14: PUT 422 — box_size 범위 초과 (ge=10.0 위반)
# ---------------------------------------------------------------------------

def test_put_box_size_out_of_range(client: TestClient) -> None:
    """PUT box_size size_x=5.0 (< 10.0) → 422 (ge=10.0 위반)."""
    body = dict(VALID_PUT_BODY)
    body["box_size"] = {"size_x": 5.0, "size_y": 5.0, "size_z": 5.0}
    resp = client.put("/api/binding_pocket/sstr2", json=body)
    assert resp.status_code == 422
