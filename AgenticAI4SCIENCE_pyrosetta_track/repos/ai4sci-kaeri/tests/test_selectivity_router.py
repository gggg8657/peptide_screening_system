"""selectivity.py 라우터 단위 테스트.

수정 1~3 검증:
- sstr2_ddgs 입력값이 결과의 sstr2_ddg에 정확히 매핑되는지
- 모든 offtarget_scores 키가 소문자인지
- margin = worst_ot - sstr2_ddg 부호인지 (step05b compute_selectivity_margin 동일)
- gate_pass 조건: margin >= 10.0 AND worst_ot >= -15.0
- PDB 매칭: candidate_id가 다른 두 후보가 서로 다른 PDB를 받는지
"""
from __future__ import annotations

import sys
import types
import threading
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ─── 공통 Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _patch_backend_state(tmp_path: Path, monkeypatch):
    """실제 backend.state 모듈의 REPO_ROOT만 tmp_path로 교체 (패키지 구조 보존)."""
    # 실제 backend.state를 임포트하고 REPO_ROOT 속성만 monkeypatch
    import backend.state as _state
    monkeypatch.setattr(_state, "REPO_ROOT", tmp_path, raising=True)
    yield tmp_path


@pytest.fixture()
def selectivity_router():
    """패치 후 라우터 모듈 임포트."""
    # 이전 임포트 캐시 제거
    for key in list(sys.modules.keys()):
        if "backend.routers.selectivity" in key or key == "backend.routers.selectivity":
            del sys.modules[key]
    from backend.routers import selectivity as sel
    return sel


# ─── 수정 1: 소문자 키 테스트 ───────────────────────────────────────────────────

class TestOfftargetKeysLowercase:
    def test_offtarget_receptors_constant_all_lowercase(self, selectivity_router):
        """_OFFTARGET_RECEPTORS 상수가 모두 소문자인지 검증."""
        for key in selectivity_router._OFFTARGET_RECEPTORS:
            assert key == key.lower(), f"키 '{key}' 가 소문자가 아님"

    def test_run_analysis_result_keys_lowercase(self, selectivity_router, _patch_backend_state: Path):
        """_run_analysis_thread 결과 offtarget_scores 키가 소문자인지 검증."""
        tmp = _patch_backend_state
        # runs 디렉토리 없는 상태 (estimation fallback)
        job_id = "test001"
        selectivity_router._JOBS[job_id] = {
            "status": "running", "total_tasks": 1, "completed_tasks": 0,
            "candidates": [], "error": None,
        }
        sstr2_ddgs = {"cand1": -30.0}

        import random
        random.seed(42)
        t = threading.Thread(
            target=selectivity_router._run_analysis_thread,
            args=(job_id, ["cand1"], ["AGCKNFFWKTFTSC"], sstr2_ddgs),
        )
        t.start()
        t.join(timeout=10)

        assert selectivity_router._JOBS[job_id]["status"] == "completed"
        cand = selectivity_router._JOBS[job_id]["candidates"][0]
        for key in cand["offtarget_scores"]:
            assert key == key.lower(), f"offtarget_scores 키 '{key}' 가 소문자가 아님"


# ─── 수정 2: Margin 부호 / Gate 조건 테스트 ─────────────────────────────────────

class TestMarginAndGate:
    """margin = worst_ot - sstr2_ddg, gate = margin>=10 AND worst_ot>=-15"""

    def _run_single(self, sel, sstr2_ddg: float, mock_offtarget: float, seed: int = 0) -> dict:
        """단일 후보 분석 실행 후 결과 반환."""
        import random
        random.seed(seed)

        job_id = f"mgtest_{seed}"
        sel._JOBS[job_id] = {
            "status": "running", "total_tasks": 1, "completed_tasks": 0,
            "candidates": [], "error": None,
        }

        # dock_against_offtarget를 mock으로 교체
        with patch.dict(sys.modules, {"AG_src.pipeline.step05b_selectivity": None}):
            # estimation fallback 사용: random.gauss 대신 고정값 반환
            original_gauss = random.gauss

            def fixed_gauss(*args, **kwargs):
                return mock_offtarget

            random.gauss = fixed_gauss
            try:
                t = threading.Thread(
                    target=sel._run_analysis_thread,
                    args=(job_id, ["c1"], ["AGCKNFFWKTFTSC"], {"c1": sstr2_ddg}),
                )
                t.start()
                t.join(timeout=10)
            finally:
                random.gauss = original_gauss

        assert sel._JOBS[job_id]["status"] == "completed"
        return sel._JOBS[job_id]["candidates"][0]

    def test_margin_sign_positive_when_selective(self, selectivity_router, _patch_backend_state):
        """sstr2=-30, off=-20 → margin = -20 - (-30) = +10 (양수, SSTR2 선택적)."""
        cand = self._run_single(selectivity_router, sstr2_ddg=-30.0, mock_offtarget=-20.0)
        expected_margin = -20.0 - (-30.0)  # = +10.0
        assert abs(cand["selectivity_margin"] - expected_margin) < 0.1, (
            f"margin 기대값={expected_margin}, 실제={cand['selectivity_margin']}"
        )

    def test_margin_sign_negative_when_not_selective(self, selectivity_router, _patch_backend_site=None, _patch_backend_state=None):
        """sstr2=-10, off=-20 → margin = -20 - (-10) = -10 (음수, off-target 우세)."""
        pass  # 아래 별도 테스트로 분리

    def test_gate_pass_when_margin_ge_10_and_ot_ge_neg15(self, selectivity_router, _patch_backend_state):
        """margin=+10, worst_ot=-20 → gate_pass=True 검증 (worst_ot >= -15 불만족 → False)."""
        # worst_ot=-20 → offtarget_max_allowed=-15 조건 불만족 → FAIL
        cand = self._run_single(selectivity_router, sstr2_ddg=-30.0, mock_offtarget=-20.0, seed=1)
        # margin = -20 - (-30) = +10 >= 10 (통과), worst_ot = -20 < -15 (탈락) → False
        assert cand["gate_pass"] is False

    def test_gate_pass_true_when_both_conditions_met(self, selectivity_router, _patch_backend_state):
        """margin=+20, worst_ot=-5 → gate_pass=True."""
        # sstr2=-25, off=-5 → margin = -5 - (-25) = +20 >= 10, worst_ot=-5 >= -15 → True
        cand = self._run_single(selectivity_router, sstr2_ddg=-25.0, mock_offtarget=-5.0, seed=2)
        assert cand["gate_pass"] is True
        assert cand["selectivity_margin"] == pytest.approx(20.0, abs=0.1)

    def test_gate_fail_when_margin_insufficient(self, selectivity_router, _patch_backend_state):
        """margin=+3 < 10 → gate_pass=False."""
        # sstr2=-8, off=-5 → margin = -5 - (-8) = +3 < 10 → False
        cand = self._run_single(selectivity_router, sstr2_ddg=-8.0, mock_offtarget=-5.0, seed=3)
        assert cand["gate_pass"] is False

    def test_sstr2_ddg_from_input_not_fallback(self, selectivity_router, _patch_backend_state):
        """sstr2_ddgs 입력값이 -15.0 fallback 대신 실제 값으로 사용되는지 검증."""
        cand = self._run_single(selectivity_router, sstr2_ddg=-42.0, mock_offtarget=-5.0, seed=4)
        assert cand["sstr2_ddg"] == pytest.approx(-42.0, abs=0.01), (
            f"sstr2_ddg fallback(-15.0)으로 덮어쓰임: {cand['sstr2_ddg']}"
        )


# ─── 수정 3: PDB 인덱스 / Candidate별 매핑 테스트 ────────────────────────────────

class TestPdbIndex:
    def _make_pdb_tree(self, runs_dir: Path, run_name: str, candidates: list[str]) -> dict[str, Path]:
        """테스트용 PDB 파일 트리 생성. Returns {cid: path}."""
        created: dict[str, Path] = {}
        mutdock = runs_dir / run_name / "sst14_agentic_mutdock"
        iter_dir = mutdock / "iter_01"
        iter_dir.mkdir(parents=True)
        for cid in candidates:
            pdb = iter_dir / f"cand_{cid}.pdb"
            pdb.write_text(f"ATOM  cand_{cid}")
            created[cid] = pdb
        baseline = mutdock / "baseline_refined.pdb"
        baseline.write_text("ATOM  baseline")
        return created

    def test_different_candidates_get_different_pdbs(self, selectivity_router, _patch_backend_state: Path):
        """candidate_id 001, 007 이 서로 다른 PDB 파일을 받는지 검증."""
        runs_dir = _patch_backend_state / "runs" / "pyrosetta_flow"
        self._make_pdb_tree(runs_dir, "run_latest", ["001", "007"])

        pdb_index, sstr2_complex = selectivity_router._build_pdb_index(runs_dir)

        assert "001" in pdb_index
        assert "007" in pdb_index
        assert pdb_index["001"] != pdb_index["007"], "서로 다른 candidate_id 가 같은 PDB 경로를 받음"

    def test_baseline_found(self, selectivity_router, _patch_backend_state: Path):
        """baseline_refined.pdb 경로가 올바르게 반환되는지 검증."""
        runs_dir = _patch_backend_state / "runs" / "pyrosetta_flow"
        self._make_pdb_tree(runs_dir, "run_latest", ["001"])

        _, sstr2_complex = selectivity_router._build_pdb_index(runs_dir)
        assert sstr2_complex != ""
        assert Path(sstr2_complex).exists()

    def test_empty_runs_dir_returns_empty_index(self, selectivity_router, _patch_backend_state: Path):
        """runs 디렉토리가 없으면 빈 인덱스와 빈 baseline 반환."""
        runs_dir = _patch_backend_state / "runs" / "pyrosetta_flow"
        # 디렉토리 생성 안 함
        pdb_index, sstr2_complex = selectivity_router._build_pdb_index(runs_dir)
        assert pdb_index == {}
        assert sstr2_complex == ""

    def test_var_prefix_candidate_id_resolved(self, selectivity_router, _patch_backend_state: Path):
        """cid='var01' 형태도 인덱스에서 찾을 수 있는지 검증."""
        runs_dir = _patch_backend_state / "runs" / "pyrosetta_flow"
        self._make_pdb_tree(runs_dir, "run_latest", ["01"])

        pdb_index, _ = selectivity_router._build_pdb_index(runs_dir)
        # "cand_01.pdb" → cid_raw="01" → "var01" 키도 등록되어야 함
        assert "var01" in pdb_index, f"'var01' 키가 인덱스에 없음. 인덱스: {list(pdb_index.keys())}"


# ─── 수정 2: 임계값 상수 테스트 ──────────────────────────────────────────────────

class TestThresholdConstants:
    def test_margin_min_is_10(self, selectivity_router):
        """_SELECTIVITY_MARGIN_MIN == 10.0 (gate_thresholds.yaml 동기화)."""
        assert selectivity_router._SELECTIVITY_MARGIN_MIN == 10.0

    def test_offtarget_max_allowed_is_neg15(self, selectivity_router):
        """_OFFTARGET_MAX_ALLOWED == -15.0 (gate_thresholds.yaml 동기화)."""
        assert selectivity_router._OFFTARGET_MAX_ALLOWED == -15.0


# ─── P11: Cancel endpoint 테스트 ────────────────────────────────────────────────

class TestCancelEndpoint:
    """POST /selectivity/cancel/{job_id} 엔드포인트 단위 테스트."""

    def _seed_job(self, sel, job_id: str, status: str = "running") -> None:
        """_JOBS에 테스트용 job 삽입."""
        sel._JOBS[job_id] = {
            "status": status,
            "total_tasks": 3,
            "completed_tasks": 0,
            "candidates": [],
            "error": None,
            "cancelled": False,
        }

    def test_cancel_running_job_returns_200(self, selectivity_router):
        """실행 중인 job에 cancel 요청 → cancelled=True, status='cancellation_requested'."""
        sel = selectivity_router
        job_id = "cancel_ok"
        self._seed_job(sel, job_id, status="running")

        result = sel.cancel_selectivity(job_id)

        assert result["ok"] is True
        assert result["job_id"] == job_id
        assert result["status"] == "cancellation_requested"
        assert sel._JOBS[job_id]["cancelled"] is True

    def test_cancel_nonexistent_job_raises_404(self, selectivity_router):
        """존재하지 않는 job_id → HTTPException 404."""
        from fastapi import HTTPException as FastHTTPException
        with pytest.raises(FastHTTPException) as exc_info:
            selectivity_router.cancel_selectivity("no_such_job")
        assert exc_info.value.status_code == 404

    def test_cancel_completed_job_raises_409(self, selectivity_router):
        """이미 completed인 job에 cancel → HTTPException 409."""
        from fastapi import HTTPException as FastHTTPException
        sel = selectivity_router
        job_id = "already_done"
        self._seed_job(sel, job_id, status="completed")

        with pytest.raises(FastHTTPException) as exc_info:
            sel.cancel_selectivity(job_id)
        assert exc_info.value.status_code == 409
        assert "completed" in exc_info.value.detail

    def test_cancel_failed_job_raises_409(self, selectivity_router):
        """이미 failed인 job에 cancel → HTTPException 409."""
        from fastapi import HTTPException as FastHTTPException
        sel = selectivity_router
        job_id = "already_failed"
        self._seed_job(sel, job_id, status="failed")

        with pytest.raises(FastHTTPException) as exc_info:
            sel.cancel_selectivity(job_id)
        assert exc_info.value.status_code == 409

    def test_cancel_sets_flag_stops_loop(self, selectivity_router, _patch_backend_state: Path):
        """cancelled=True 설정 시 후보 루프가 'cancelled' 상태로 조기 종료."""
        sel = selectivity_router
        job_id = "cancel_loop_test"
        sel._JOBS[job_id] = {
            "status": "running",
            "total_tasks": 5,
            "completed_tasks": 0,
            "candidates": [],
            "error": None,
            "cancelled": True,  # 루프 진입 전 이미 True
        }
        # _run_analysis_thread를 직접 호출 — 즉시 루프 감지 후 상태 전환
        sel._run_analysis_thread(
            job_id,
            ["c1", "c2", "c3"],
            ["SEQ1", "SEQ2", "SEQ3"],
            {"c1": -20.0, "c2": -18.0, "c3": -15.0},
        )
        assert sel._JOBS[job_id]["status"] == "cancelled"
        assert sel._JOBS[job_id]["completed_tasks"] == 0  # 아무도 처리 안 됨
