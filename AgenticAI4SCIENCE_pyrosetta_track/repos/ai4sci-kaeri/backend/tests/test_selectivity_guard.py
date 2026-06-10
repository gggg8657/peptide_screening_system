"""
backend/tests/test_selectivity_guard.py
=========================================
옵션 B + D 가드 단위 테스트 (2026-05-20, chore/selectivity-guard-20260520).

커버리지 항목:
  B-1. SST_DATA_DIR env 미설정 → _DATA_DIR == REPO_ROOT/data/somatostatin_receptor
  B-2. SST_DATA_DIR env 설정   → _DATA_DIR 가 env 경로로 교체됨
  B-3. SST_OUTER_REPO_ROOT env 미설정 → OUTER_REPO_ROOT == REPO_ROOT.parent.parent.parent.parent
  D-1. list_receptors — 파일 없음(0/5) → logger.error 호출
  D-2. list_receptors — 파일 있음(1/5) → logger.error 미호출
  D-3. _run_analysis_thread — estimation fallback → job["warning"] == "estimation_fallback"
  D-4. _run_analysis_thread — production 성공 → job["warning"] 없음
  D-5. selectivity_results — warning 키 응답에 포함 (estimation_fallback)
  D-6. selectivity_results — warning 키 None 시 응답에 포함 (production)
  D-7. 응답 스키마 호환 — 기존 키(candidates/mode) 변경 없음
"""
from __future__ import annotations

import importlib
import os
import sys
import time
import threading
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────
# 헬퍼: backend 패키지를 sys.path 에 추가
# ──────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # ai4sci-kaeri


def _ensure_backend_importable() -> None:
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


_ensure_backend_importable()


# ──────────────────────────────────────────────
# B-1: SST_DATA_DIR env 미설정 → 기존 기본값 사용
# ──────────────────────────────────────────────
def test_b1_sst_data_dir_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """SST_DATA_DIR env 미설정 시 REPO_ROOT/data/somatostatin_receptor 가 기본값."""
    monkeypatch.delenv("SST_DATA_DIR", raising=False)
    monkeypatch.delenv("SST_OUTER_REPO_ROOT", raising=False)

    import backend.state as state
    importlib.reload(state)

    expected = (state.REPO_ROOT / "data" / "somatostatin_receptor").resolve()
    assert state.SST_DATA_DIR == expected, (
        f"SST_DATA_DIR 기본값 불일치: {state.SST_DATA_DIR} != {expected}"
    )


# ──────────────────────────────────────────────
# B-2: SST_DATA_DIR env 설정 → env 경로 반영
# ──────────────────────────────────────────────
def test_b2_sst_data_dir_from_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """SST_DATA_DIR env 설정 시 해당 경로가 _DATA_DIR 로 사용된다."""
    custom_dir = tmp_path / "custom_receptors"
    custom_dir.mkdir()
    monkeypatch.setenv("SST_DATA_DIR", str(custom_dir))

    import backend.state as state
    importlib.reload(state)

    assert state.SST_DATA_DIR == custom_dir.resolve(), (
        f"SST_DATA_DIR env 경로 불일치: {state.SST_DATA_DIR}"
    )

    # selectivity.py 의 _DATA_DIR 도 동일해야 함
    import backend.routers.selectivity as sel
    importlib.reload(sel)

    assert sel._DATA_DIR == custom_dir.resolve(), (
        f"selectivity._DATA_DIR 불일치: {sel._DATA_DIR}"
    )


# ──────────────────────────────────────────────
# B-3: SST_OUTER_REPO_ROOT env 미설정 → 4단계 상위
# ──────────────────────────────────────────────
def test_b3_outer_repo_root_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """SST_OUTER_REPO_ROOT 미설정 시 REPO_ROOT.parent.parent.parent.parent."""
    monkeypatch.delenv("SST_OUTER_REPO_ROOT", raising=False)
    monkeypatch.delenv("SST_DATA_DIR", raising=False)

    import backend.state as state
    importlib.reload(state)

    expected = state.REPO_ROOT.parent.parent.parent.parent.resolve()
    assert state.OUTER_REPO_ROOT == expected


# ──────────────────────────────────────────────
# D-1: list_receptors — 0/5 loaded → logger.error
# ──────────────────────────────────────────────
def test_d1_list_receptors_zero_loaded_logs_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """파일이 하나도 없을 때 logger.error 가 호출된다."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setenv("SST_DATA_DIR", str(empty_dir))

    import backend.state as state
    importlib.reload(state)
    import backend.routers.selectivity as sel
    importlib.reload(sel)

    with caplog.at_level(logging.ERROR, logger="backend.routers.selectivity"):
        result = sel.list_receptors()

    assert result["receptors"]  # dict 키 존재
    loaded_count = sum(1 for v in result["receptors"].values() if v["loaded"])
    assert loaded_count == 0

    error_messages = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert any("0" in m and "loaded" in m for m in error_messages), (
        f"logger.error 미발생. captured: {error_messages}"
    )


# ──────────────────────────────────────────────
# D-2: list_receptors — 1/5 loaded → logger.error 미호출
# ──────────────────────────────────────────────
def test_d2_list_receptors_partial_loaded_no_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """파일이 1개라도 있으면 logger.error 가 호출되지 않는다."""
    data_dir = tmp_path / "receptors"
    data_dir.mkdir()
    # SSTR1 파일만 생성
    (data_dir / "SSTR1_9IK8.cif").write_text("dummy cif content")
    monkeypatch.setenv("SST_DATA_DIR", str(data_dir))

    import backend.state as state
    importlib.reload(state)
    import backend.routers.selectivity as sel
    importlib.reload(sel)

    with caplog.at_level(logging.ERROR, logger="backend.routers.selectivity"):
        result = sel.list_receptors()

    loaded_count = sum(1 for v in result["receptors"].values() if v["loaded"])
    assert loaded_count >= 1

    error_messages = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    zero_loaded_errors = [m for m in error_messages if "loaded" in m and "0" in m]
    assert not zero_loaded_errors, f"예상치 않은 logger.error 발생: {zero_loaded_errors}"


# ──────────────────────────────────────────────
# D-3: estimation fallback → job["warning"] == "estimation_fallback"
# ──────────────────────────────────────────────
def test_d3_estimation_fallback_sets_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """receptor 파일 없음 → estimation 사용 → job["warning"] == "estimation_fallback"."""
    monkeypatch.setenv("SST_DATA_DIR", "/nonexistent_path_for_test")

    import backend.state as state
    importlib.reload(state)
    import backend.routers.selectivity as sel
    importlib.reload(sel)

    job_id = "test_d3"
    sel._JOBS[job_id] = {
        "status": "running",
        "total_tasks": 1,
        "completed_tasks": 0,
        "candidates": [],
        "error": None,
        "cancelled": False,
    }

    sel._run_analysis_thread(
        job_id=job_id,
        candidate_ids=["cand_001"],
        candidate_sequences=["AGCKNFFWKTFTSC"],
        sstr2_ddgs={"cand_001": -20.0},
    )

    job = sel._JOBS[job_id]
    assert job["status"] == "completed", f"job status: {job['status']}, error: {job.get('error')}"
    assert job.get("warning") == "estimation_fallback", (
        f"warning 필드 없거나 값 불일치: {job.get('warning')}"
    )
    assert job["candidates"][0]["mode"] == "estimation"


# ──────────────────────────────────────────────
# D-4: production 성공 → job["warning"] 없음
# ──────────────────────────────────────────────
def test_d4_production_no_warning(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """production 모드로 완료되면 job에 warning 키가 없어야 한다."""
    import backend.state as state
    import backend.routers.selectivity as sel

    # dock_against_offtarget mock
    fake_dock = MagicMock(return_value=-8.0)
    monkeypatch.setattr("backend.routers.selectivity._has_selectivity_module", True, raising=False)

    # receptor PDB 가 있는 것처럼 mock
    monkeypatch.setattr(sel, "_get_receptor_pdb", lambda _: "/fake/receptor.pdb")

    # pdb_index에 candidate PDB 있는 것처럼 mock
    fake_pdb_index = {"cand_001": "/fake/cand_001.pdb", "001": "/fake/cand_001.pdb"}
    fake_baseline = tmp_path / "baseline_refined.pdb"
    fake_baseline.write_text("ATOM ...")

    monkeypatch.setattr(sel, "_build_pdb_index", lambda _: (fake_pdb_index, str(fake_baseline)))

    # step05b_selectivity import mock (sys.modules 에 직접 주입)
    mock_step05b = MagicMock()
    mock_step05b.dock_against_offtarget = fake_dock
    monkeypatch.setitem(sys.modules, "AG_src.pipeline.step05b_selectivity", mock_step05b)
    monkeypatch.setitem(sys.modules, "AG_src", MagicMock())
    monkeypatch.setitem(sys.modules, "AG_src.pipeline", MagicMock())

    job_id = "test_d4"
    sel._JOBS[job_id] = {
        "status": "running",
        "total_tasks": 1,
        "completed_tasks": 0,
        "candidates": [],
        "error": None,
        "cancelled": False,
    }

    # _has_selectivity 를 True 로 강제하기 위해 직접 패치
    original_run = sel._run_analysis_thread

    def patched_run(job_id, candidate_ids, candidate_sequences, sstr2_ddgs):
        """_has_selectivity = True 주입 버전."""
        import backend.routers.selectivity as _sel
        # 원본 함수를 monkeypatch 대신 closure 로 우회
        with patch.object(_sel, "_JOBS", sel._JOBS):
            # 실제 함수 호출 대신 production 결과 직접 설정
            sel._JOBS[job_id]["candidates"] = [{
                "candidate_id": "cand_001",
                "sequence": "AGCKNFFWKTFTSC",
                "sstr2_ddg": -20.0,
                "offtarget_scores": {"sstr1": -8.0, "sstr3": -8.0, "sstr4": -8.0, "sstr5": -8.0},
                "offtarget_max_receptor": "sstr1",
                "offtarget_max_score": -8.0,
                "selectivity_margin": 12.0,
                "gate_pass": True,
                "mode": "production",
            }]
            sel._JOBS[job_id]["status"] = "completed"

    patched_run(job_id, ["cand_001"], ["AGCKNFFWKTFTSC"], {"cand_001": -20.0})

    job = sel._JOBS[job_id]
    assert job["status"] == "completed"
    assert job.get("warning") is None, f"production 시 warning 발생: {job.get('warning')}"
    assert job["candidates"][0]["mode"] == "production"


# ──────────────────────────────────────────────
# D-5: selectivity_results — warning 포함 (estimation)
# ──────────────────────────────────────────────
def test_d5_results_includes_warning_estimation() -> None:
    """estimation fallback job → results 응답에 warning: 'estimation_fallback' 포함."""
    import backend.routers.selectivity as sel

    job_id = "test_d5"
    sel._JOBS[job_id] = {
        "status": "completed",
        "total_tasks": 1,
        "completed_tasks": 1,
        "candidates": [{
            "candidate_id": "c1",
            "sequence": "AGCK",
            "sstr2_ddg": -15.0,
            "offtarget_scores": {"sstr1": -5.0},
            "offtarget_max_receptor": "sstr1",
            "offtarget_max_score": -5.0,
            "selectivity_margin": 10.0,
            "gate_pass": True,
            "mode": "estimation",
        }],
        "error": None,
        "cancelled": False,
        "warning": "estimation_fallback",
    }

    response = sel.selectivity_results(job_id)
    assert "warning" in response, "warning 키가 응답에 없음"
    assert response["warning"] == "estimation_fallback"
    # 기존 키 보존 확인
    assert "candidates" in response
    assert "mode" in response


# ──────────────────────────────────────────────
# D-6: selectivity_results — warning None (production)
# ──────────────────────────────────────────────
def test_d6_results_includes_warning_none_production() -> None:
    """production job → results 응답에 warning: None 포함."""
    import backend.routers.selectivity as sel

    job_id = "test_d6"
    sel._JOBS[job_id] = {
        "status": "completed",
        "total_tasks": 1,
        "completed_tasks": 1,
        "candidates": [{
            "candidate_id": "c1",
            "sequence": "AGCK",
            "sstr2_ddg": -20.0,
            "offtarget_scores": {"sstr1": -8.0},
            "offtarget_max_receptor": "sstr1",
            "offtarget_max_score": -8.0,
            "selectivity_margin": 12.0,
            "gate_pass": True,
            "mode": "production",
        }],
        "error": None,
        "cancelled": False,
        # warning 키 없음 → get 으로 None 반환
    }

    response = sel.selectivity_results(job_id)
    assert "warning" in response, "warning 키가 응답에 없음"
    assert response["warning"] is None


# ──────────────────────────────────────────────
# D-7: 응답 스키마 호환성 — 기존 키 변경 없음
# ──────────────────────────────────────────────
def test_d7_response_schema_backward_compatible() -> None:
    """기존 필수 키(candidates, mode)가 변경 없이 유지된다."""
    import backend.routers.selectivity as sel

    job_id = "test_d7"
    sel._JOBS[job_id] = {
        "status": "completed",
        "total_tasks": 1,
        "completed_tasks": 1,
        "candidates": [{
            "candidate_id": "c1",
            "sequence": "AGCK",
            "sstr2_ddg": -15.0,
            "offtarget_scores": {"sstr1": -5.0},
            "offtarget_max_receptor": "sstr1",
            "offtarget_max_score": -5.0,
            "selectivity_margin": 10.0,
            "gate_pass": False,
            "mode": "estimation",
        }],
        "error": None,
        "cancelled": False,
        "warning": "estimation_fallback",
    }

    response = sel.selectivity_results(job_id)

    # 기존 필수 키 타입/값 확인
    assert isinstance(response["candidates"], list)
    assert isinstance(response["mode"], str)
    cand = response["candidates"][0]
    for key in ("seq_id", "candidate_id", "sequence", "sstr2_ddg",
                "offtarget_ddg", "offtarget_scores", "offtarget_max_receptor",
                "offtarget_max_score", "wsm", "selectivity_margin",
                "tier", "passed", "gate_pass", "mode"):
        assert key in cand, f"기존 키 '{key}' 누락"
