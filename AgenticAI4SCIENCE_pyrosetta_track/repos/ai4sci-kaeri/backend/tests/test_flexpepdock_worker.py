"""
test_flexpepdock_worker.py
===========================
FlexPepDock 워커 단위 테스트.

- ETA 학습 정확성
- Lock stale 회수
- 취소 signal 처리
- selectivity_index 계산
- build_ensemble_tar
- 수용체 PDB 경로 조회
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def patch_jobs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """모든 테스트에서 JOBS_DIR를 임시 디렉토리로 교체."""
    jobs_dir = tmp_path / "flexpepdock_jobs"
    jobs_dir.mkdir(parents=True)

    import pipeline_local.scripts.flexpepdock_worker as worker_mod
    monkeypatch.setattr(worker_mod, "JOBS_DIR", jobs_dir)
    monkeypatch.setattr(worker_mod, "LOCK_FILE", jobs_dir / ".lock")
    monkeypatch.setattr(worker_mod, "ETA_HISTORY_FILE", jobs_dir / "eta_history.json")
    return jobs_dir


# ---------------------------------------------------------------------------
# Lock stale 회수 테스트
# ---------------------------------------------------------------------------


class TestLock:
    def test_acquire_when_no_lock_file(self, patch_jobs_dir: Path):
        """lock 파일 없음 → acquire 성공."""
        from pipeline_local.scripts.flexpepdock_worker import acquire_lock, release_lock
        result = acquire_lock()
        assert result is True
        assert (patch_jobs_dir / ".lock").exists()
        release_lock()

    def test_release_removes_lock(self, patch_jobs_dir: Path):
        """acquire 후 release → lock 파일 없어짐."""
        from pipeline_local.scripts.flexpepdock_worker import acquire_lock, release_lock
        acquire_lock()
        release_lock()
        assert not (patch_jobs_dir / ".lock").exists()

    def test_stale_lock_reclaim(self, patch_jobs_dir: Path):
        """죽은 PID lock → stale 감지 후 자동 회수."""
        from pipeline_local.scripts.flexpepdock_worker import acquire_lock, release_lock
        lock_file = patch_jobs_dir / ".lock"
        lock_file.write_text(
            json.dumps({"pid": 99999999, "acquired_at": time.time()}),
            encoding="utf-8",
        )
        result = acquire_lock()
        assert result is True
        data = json.loads(lock_file.read_text(encoding="utf-8"))
        assert data["pid"] == os.getpid()
        release_lock()

    def test_live_pid_blocks(self, patch_jobs_dir: Path):
        """현재 프로세스 PID lock → 재 acquire 실패."""
        from pipeline_local.scripts.flexpepdock_worker import acquire_lock
        lock_file = patch_jobs_dir / ".lock"
        lock_file.write_text(
            json.dumps({"pid": os.getpid(), "acquired_at": time.time()}),
            encoding="utf-8",
        )
        result = acquire_lock()
        assert result is False
        # cleanup
        lock_file.unlink()

    def test_release_skips_if_wrong_pid(self, patch_jobs_dir: Path):
        """다른 PID의 lock → release가 삭제 안 함."""
        from pipeline_local.scripts.flexpepdock_worker import release_lock
        lock_file = patch_jobs_dir / ".lock"
        lock_file.write_text(
            json.dumps({"pid": 99999999}),
            encoding="utf-8",
        )
        release_lock()
        # 다른 PID 소유 lock → 삭제되면 안 됨
        assert lock_file.exists()
        lock_file.unlink()


# ---------------------------------------------------------------------------
# ETA 학습 테스트
# ---------------------------------------------------------------------------


class TestEtaHistory:
    def test_no_history_returns_default(self, patch_jobs_dir: Path):
        """이력 없음 → 30min × n_receptors."""
        from pipeline_local.scripts.flexpepdock_worker import estimate_eta
        eta = estimate_eta(n_receptors=3, nstruct=50)
        assert eta == 3 * 30 * 60

    def test_few_history_returns_default(self, patch_jobs_dir: Path):
        """이력 4건 (<5) → 보수적 기본값."""
        from pipeline_local.scripts.flexpepdock_worker import estimate_eta, save_eta_history
        history = [
            {"job_id": f"j{i}", "n_receptors": 1, "nstruct": 50,
             "elapsed_sec": 600.0, "recorded_at": "2026-05-15T00:00:00Z"}
            for i in range(4)
        ]
        save_eta_history(history)
        eta = estimate_eta(n_receptors=1, nstruct=50)
        assert eta == 1 * 30 * 60  # 여전히 기본값

    def test_sufficient_history_learns(self, patch_jobs_dir: Path):
        """이력 5건 → 평균 기반 학습."""
        from pipeline_local.scripts.flexpepdock_worker import estimate_eta, save_eta_history
        history = [
            {"job_id": f"j{i}", "n_receptors": 1, "nstruct": 50,
             "elapsed_sec": 600.0, "recorded_at": "2026-05-15T00:00:00Z"}
            for i in range(5)
        ]
        save_eta_history(history)
        eta = estimate_eta(n_receptors=1, nstruct=50)
        # 평균 600초 × 1 receptor
        assert 550 <= eta <= 650

    def test_eta_scales_with_nstruct(self, patch_jobs_dir: Path):
        """nstruct 두 배 → ETA 두 배."""
        from pipeline_local.scripts.flexpepdock_worker import estimate_eta, save_eta_history
        history = [
            {"job_id": f"j{i}", "n_receptors": 1, "nstruct": 50,
             "elapsed_sec": 600.0, "recorded_at": "2026-05-15T00:00:00Z"}
            for i in range(5)
        ]
        save_eta_history(history)
        eta_50 = estimate_eta(n_receptors=1, nstruct=50)
        eta_100 = estimate_eta(n_receptors=1, nstruct=100)
        assert abs(eta_100 / eta_50 - 2.0) < 0.5

    def test_eta_scales_with_receptors(self, patch_jobs_dir: Path):
        """receptor 두 배 → ETA 두 배."""
        from pipeline_local.scripts.flexpepdock_worker import estimate_eta, save_eta_history
        history = [
            {"job_id": f"j{i}", "n_receptors": 1, "nstruct": 50,
             "elapsed_sec": 600.0, "recorded_at": "2026-05-15T00:00:00Z"}
            for i in range(5)
        ]
        save_eta_history(history)
        eta_1 = estimate_eta(n_receptors=1, nstruct=50)
        eta_2 = estimate_eta(n_receptors=2, nstruct=50)
        assert abs(eta_2 / eta_1 - 2.0) < 0.5

    def test_record_eta_history(self, patch_jobs_dir: Path):
        """record_eta_history가 ETA_HISTORY_FILE에 누적한다."""
        from pipeline_local.scripts.flexpepdock_worker import (
            record_eta_history, load_eta_history
        )
        record_eta_history(n_receptors=2, nstruct=50, elapsed_sec=1200.0, job_id="test-job")
        history = load_eta_history()
        assert len(history) == 1
        assert history[0]["job_id"] == "test-job"
        assert history[0]["elapsed_sec"] == 1200.0

    def test_history_capped_at_100(self, patch_jobs_dir: Path):
        """이력 100건 초과 시 최근 100건만 유지."""
        from pipeline_local.scripts.flexpepdock_worker import (
            record_eta_history, load_eta_history
        )
        for i in range(105):
            record_eta_history(n_receptors=1, nstruct=50, elapsed_sec=600.0, job_id=f"j{i}")
        history = load_eta_history()
        assert len(history) == 100
        # 가장 최근 job_id가 마지막에 있어야 함
        assert history[-1]["job_id"] == "j104"


# ---------------------------------------------------------------------------
# selectivity_index 계산 테스트
# ---------------------------------------------------------------------------


class TestSelectivityIndex:
    def _call(self, matrix: list[dict]) -> float:
        from pipeline_local.scripts.flexpepdock_worker import _compute_selectivity_index
        return _compute_selectivity_index(matrix)

    def test_sstr2_strongest(self):
        """SSTR2 dG가 가장 낮음 → 양수 selectivity_index."""
        matrix = [
            {"receptor": "SSTR2", "dG_kcal_mol": -11.5},
            {"receptor": "SSTR1", "dG_kcal_mol": -8.2},
            {"receptor": "SSTR3", "dG_kcal_mol": -7.0},
        ]
        si = self._call(matrix)
        # max(others) - sstr2_dg = -7.0 - (-11.5) = 4.5
        assert abs(si - 4.5) < 1e-9

    def test_no_sstr2_returns_zero(self):
        """SSTR2 없음 → 0.0."""
        matrix = [
            {"receptor": "SSTR1", "dG_kcal_mol": -8.2},
        ]
        si = self._call(matrix)
        assert si == 0.0

    def test_no_others_returns_zero(self):
        """SSTR2만 있음 → 0.0."""
        matrix = [
            {"receptor": "SSTR2", "dG_kcal_mol": -11.5},
        ]
        si = self._call(matrix)
        assert si == 0.0

    def test_empty_matrix(self):
        """빈 matrix → 0.0."""
        si = self._call([])
        assert si == 0.0

    def test_negative_selectivity(self):
        """SSTR2가 다른 수용체보다 약한 결합 → 음수 index."""
        matrix = [
            {"receptor": "SSTR2", "dG_kcal_mol": -5.0},
            {"receptor": "SSTR1", "dG_kcal_mol": -12.0},
        ]
        si = self._call(matrix)
        # max(others) = -12.0, sstr2 = -5.0 → index = -12.0 - (-5.0) = -7.0
        assert abs(si - (-7.0)) < 1e-9


# ---------------------------------------------------------------------------
# 취소 signal 테스트
# ---------------------------------------------------------------------------


class TestCancellationSignal:
    def test_cancel_flag_stops_processing(self, patch_jobs_dir: Path):
        """cancel_flag[0]=True 시 _process_job이 failed로 종료."""
        import pipeline_local.scripts.flexpepdock_worker as worker_mod

        job_id = "cancel-test"
        job_dir = patch_jobs_dir / job_id
        job_dir.mkdir()
        (job_dir / "job.json").write_text(
            json.dumps({
                "sequence": "AGCKNFFWKTFTSC",
                "receptors": ["SSTR1", "SSTR2"],
                "config": {"cycles": 1, "nstruct": 1},
            }),
            encoding="utf-8",
        )
        (job_dir / "status.json").write_text(
            json.dumps({"state": "queued", "progress": 0.0, "eta_seconds": 0}),
            encoding="utf-8",
        )

        call_count = [0]

        def mock_flexpepdock(*args, **kwargs):
            # 첫 번째 receptor 처리 후 cancel_flag 설정
            call_count[0] += 1
            if call_count[0] >= 1:
                kwargs.get("cancel_flag", [False]).__setitem__(0, True)
            return {"receptor": "SSTR1", "dG_kcal_mol": -8.0, "interface_score": -40.0, "pass": True, "pdb_paths": []}

        with (
            patch.object(worker_mod, "_run_flexpepdock_for_receptor", mock_flexpepdock),
            patch.object(worker_mod, "get_receptor_pdb_path", return_value="/fake/path.pdb"),
        ):
            cancel_flag: list[bool] = [False]
            # cancelling 상태로 미리 설정 (워커 polling 방식 시뮬레이션)
            (job_dir / "status.json").write_text(
                json.dumps({"state": "cancelling", "progress": 0.0, "eta_seconds": 0}),
                encoding="utf-8",
            )
            worker_mod._process_job(job_id, cancel_flag)

        final_status = json.loads(
            (job_dir / "status.json").read_text(encoding="utf-8")
        )
        assert final_status["state"] == "failed"

    def test_cancelling_state_detected_by_worker(self, patch_jobs_dir: Path):
        """status.json state=cancelling → 워커가 다음 수용체에서 감지."""
        import pipeline_local.scripts.flexpepdock_worker as worker_mod

        job_id = "cancel-state-test"
        job_dir = patch_jobs_dir / job_id
        job_dir.mkdir()
        (job_dir / "job.json").write_text(
            json.dumps({
                "sequence": "AGCKNFFWKTFTSC",
                "receptors": ["SSTR2"],
                "config": {"cycles": 1, "nstruct": 1},
            }),
            encoding="utf-8",
        )
        # 처음부터 cancelling 상태로 시작
        (job_dir / "status.json").write_text(
            json.dumps({"state": "cancelling", "progress": 0.0, "eta_seconds": 0}),
            encoding="utf-8",
        )

        with patch.object(worker_mod, "get_receptor_pdb_path", return_value="/fake/path.pdb"):
            cancel_flag: list[bool] = [False]
            worker_mod._process_job(job_id, cancel_flag)

        final_status = json.loads(
            (job_dir / "status.json").read_text(encoding="utf-8")
        )
        assert final_status["state"] == "failed"
        assert "취소" in final_status.get("error_message", "")


# ---------------------------------------------------------------------------
# build_ensemble_tar 테스트
# ---------------------------------------------------------------------------


class TestEnsembleTar:
    def test_no_ensemble_dir_returns_none(self, patch_jobs_dir: Path):
        """ensemble 디렉토리 없음 → None."""
        from pipeline_local.scripts.flexpepdock_worker import build_ensemble_tar
        result = build_ensemble_tar("nonexistent-job")
        assert result is None

    def test_tar_created(self, patch_jobs_dir: Path, tmp_path: Path):
        """ensemble 디렉토리 있음 → tar.gz 생성."""
        import tarfile
        from pipeline_local.scripts.flexpepdock_worker import build_ensemble_tar

        job_id = "tar-test"
        ensemble_dir = patch_jobs_dir / job_id / "ensemble" / "SSTR2"
        ensemble_dir.mkdir(parents=True)
        (ensemble_dir / "model_0.pdb").write_text("ATOM ...", encoding="utf-8")

        tar_path = build_ensemble_tar(job_id)
        assert tar_path is not None
        assert tar_path.exists()
        assert tar_path.suffix == ".gz"

        # tar 내용 확인
        with tarfile.open(tar_path, "r:gz") as tf:
            names = tf.getnames()
        assert any("model_0.pdb" in n for n in names)


# ---------------------------------------------------------------------------
# 수용체 PDB 경로 조회 테스트
# ---------------------------------------------------------------------------


class TestGetReceptorPdbPath:
    def test_existing_receptor(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """존재하는 수용체 PDB → 경로 반환."""
        import pipeline_local.scripts.flexpepdock_worker as worker_mod

        # 임시 PDB 파일 생성
        pdb_file = tmp_path / "SSTR2_7XNA.pdb"
        pdb_file.write_text("ATOM ...", encoding="utf-8")

        # 검색 경로 주입
        monkeypatch.setattr(
            worker_mod,
            "_RECEPTOR_SEARCH_PATHS",
            [("test", str(tmp_path / "{name}_{pdb_id}.pdb"))],
        )

        path = worker_mod.get_receptor_pdb_path("SSTR2")
        assert path is not None
        assert "SSTR2_7XNA.pdb" in path

    def test_missing_receptor_returns_none(self, monkeypatch: pytest.MonkeyPatch):
        """존재하지 않는 경로 → None."""
        import pipeline_local.scripts.flexpepdock_worker as worker_mod

        monkeypatch.setattr(
            worker_mod,
            "_RECEPTOR_SEARCH_PATHS",
            [("test", "/nonexistent/{name}_{pdb_id}.pdb")],
        )
        path = worker_mod.get_receptor_pdb_path("SSTR1")
        assert path is None

    def test_lowercase_receptor_normalized(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """소문자 수용체 이름 → 대문자 정규화 후 조회."""
        import pipeline_local.scripts.flexpepdock_worker as worker_mod

        pdb_file = tmp_path / "SSTR3_8XIR.pdb"
        pdb_file.write_text("ATOM ...", encoding="utf-8")
        monkeypatch.setattr(
            worker_mod,
            "_RECEPTOR_SEARCH_PATHS",
            [("test", str(tmp_path / "{name}_{pdb_id}.pdb"))],
        )
        path = worker_mod.get_receptor_pdb_path("sstr3")
        assert path is not None


# ---------------------------------------------------------------------------
# preflight_check 테스트
# ---------------------------------------------------------------------------


class TestPreflightCheck:
    def test_valid_inputs(self, monkeypatch: pytest.MonkeyPatch):
        """유효한 시퀀스 + 수용체 PDB 있음 → (True, '')."""
        import pipeline_local.scripts.flexpepdock_worker as worker_mod
        monkeypatch.setattr(worker_mod, "get_receptor_pdb_path", lambda r: "/fake/path.pdb")
        # PyRosetta conda check mock
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK")
            ok, err = worker_mod.preflight_check("AGCKNFFWKTFTSC", ["SSTR2"])
        assert ok is True
        assert err == ""

    def test_invalid_sequence(self):
        """유효하지 않은 시퀀스 → (False, error)."""
        from pipeline_local.scripts.flexpepdock_worker import preflight_check
        ok, err = preflight_check("AGCKNFFWKTFTS", ["SSTR2"])  # 13aa
        assert ok is False
        assert "시퀀스" in err

    def test_missing_receptor_pdb(self, monkeypatch: pytest.MonkeyPatch):
        """수용체 PDB 없음 → (False, error)."""
        import pipeline_local.scripts.flexpepdock_worker as worker_mod
        monkeypatch.setattr(worker_mod, "get_receptor_pdb_path", lambda r: None)
        ok, err = worker_mod.preflight_check("AGCKNFFWKTFTSC", ["SSTR1"])
        assert ok is False
        assert "PDB" in err
