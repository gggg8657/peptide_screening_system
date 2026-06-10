"""
test_flexpepdock_router.py
===========================
FlexPepDock 라우터 엔드포인트 테스트.

- 시퀀스 검증 (길이, 아미노산, Cys3-Cys14)
- 수용체 이름 검증
- Job 생성 / 조회 / 목록 / 취소 / 삭제 흐름
- Lock 동작 (mock worker)
- wetlab order에 flexpepdock_job_id 전달
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# 프로젝트 루트 PYTHONPATH 설정
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_jobs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """JOBS_DIR를 임시 디렉토리로 교체한다."""
    jobs_dir = tmp_path / "flexpepdock_jobs"
    jobs_dir.mkdir(parents=True)

    import pipeline_local.scripts.flexpepdock_worker as worker_mod
    import backend.routers.flexpepdock as router_mod

    monkeypatch.setattr(worker_mod, "JOBS_DIR", jobs_dir)
    monkeypatch.setattr(worker_mod, "LOCK_FILE", jobs_dir / ".lock")
    monkeypatch.setattr(worker_mod, "ETA_HISTORY_FILE", jobs_dir / "eta_history.json")
    monkeypatch.setattr(router_mod, "JOBS_DIR", jobs_dir)
    monkeypatch.setattr(router_mod, "LOCK_FILE", jobs_dir / ".lock")

    return jobs_dir


@pytest.fixture()
def app(tmp_jobs_dir: Path):
    """FlexPepDock 라우터만 포함한 테스트 앱."""
    from fastapi import FastAPI
    import backend.routers.flexpepdock as router_mod

    app = FastAPI()
    app.include_router(router_mod.router, prefix="/api")
    return app


@pytest.fixture()
def client(app) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# POST /api/flexpepdock/jobs 검증 테스트
# ---------------------------------------------------------------------------


class TestJobCreationValidation:
    """시퀀스·수용체 입력 검증."""

    def _post_job(
        self,
        client: TestClient,
        sequence: str = "AGCKNFFWKTFTSC",
        receptors: list[str] | None = None,
        mock_preflight: bool = True,
    ):
        if receptors is None:
            receptors = ["SSTR2"]
        payload: dict[str, Any] = {
            "sequence": sequence,
            "receptors": receptors,
        }

        if mock_preflight:
            with (
                patch("backend.routers.flexpepdock.preflight_check", return_value=(True, "")),
                patch("backend.routers.flexpepdock._ensure_worker_running"),
            ):
                return client.post("/api/flexpepdock/jobs", json=payload)
        else:
            return client.post("/api/flexpepdock/jobs", json=payload)

    def test_valid_sst14_sequence(self, client: TestClient):
        """정상 SST-14 시퀀스 AGCKNFFWKTFTSC — 201 반환."""
        resp = self._post_job(client, sequence="AGCKNFFWKTFTSC")
        assert resp.status_code == 201
        data = resp.json()
        assert "job_id" in data
        assert "eta_seconds" in data
        assert "queue_position" in data

    def test_wrong_length_sequence(self, client: TestClient):
        """13aa 시퀀스 — 422 반환."""
        resp = self._post_job(client, sequence="AGCKNFFWKTFTS", mock_preflight=False)
        assert resp.status_code == 422

    def test_too_long_sequence(self, client: TestClient):
        """15aa 시퀀스 — 422 반환."""
        resp = self._post_job(client, sequence="AGCKNFFWKTFTSCX", mock_preflight=False)
        assert resp.status_code == 422

    def test_invalid_amino_acid(self, client: TestClient):
        """유효하지 않은 아미노산 'X' 포함 — 422."""
        resp = self._post_job(client, sequence="XGCKNFFWKTFTSC", mock_preflight=False)
        assert resp.status_code == 422

    def test_missing_cys3(self, client: TestClient):
        """Cys3 위치(index 2)가 C가 아님 — 422."""
        # AGAKNFFWKTFTSC: pos 2 = A (not C)
        resp = self._post_job(client, sequence="AGAKNFFWKTFTSC", mock_preflight=False)
        assert resp.status_code == 422

    def test_missing_cys14(self, client: TestClient):
        """Cys14 위치(index 13)가 C가 아님 — 422."""
        # AGCKNFFWKTFTSA: pos 13 = A (not C)
        resp = self._post_job(client, sequence="AGCKNFFWKTFTSA", mock_preflight=False)
        assert resp.status_code == 422

    def test_unknown_receptor(self, client: TestClient):
        """알 수 없는 수용체 — 422."""
        resp = self._post_job(client, receptors=["SSTR9"], mock_preflight=False)
        assert resp.status_code == 422

    def test_empty_receptors(self, client: TestClient):
        """수용체 목록 비어있음 — 422."""
        resp = client.post(
            "/api/flexpepdock/jobs",
            json={"sequence": "AGCKNFFWKTFTSC", "receptors": []},
        )
        assert resp.status_code == 422

    def test_preflight_failure_returns_422(self, client: TestClient):
        """preflight_check 실패 — 422 반환."""
        with patch(
            "backend.routers.flexpepdock.preflight_check",
            return_value=(False, "수용체 PDB 없음: ['SSTR1']"),
        ):
            resp = client.post(
                "/api/flexpepdock/jobs",
                json={"sequence": "AGCKNFFWKTFTSC", "receptors": ["SSTR1"]},
            )
        assert resp.status_code == 422
        assert "Pre-flight" in resp.json()["detail"]

    def test_all_five_receptors(self, client: TestClient):
        """SSTR1-5 전체 지정 — 201 반환."""
        resp = self._post_job(
            client,
            receptors=["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"],
        )
        assert resp.status_code == 201

    def test_lowercase_receptors_normalized(self, client: TestClient):
        """소문자 수용체 이름 자동 대문자화 — 201 반환."""
        resp = self._post_job(client, receptors=["sstr2", "sstr1"])
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/flexpepdock/jobs 목록 테스트
# ---------------------------------------------------------------------------


class TestJobList:
    def _create_job(self, tmp_jobs_dir: Path, job_id: str, state: str) -> None:
        """테스트용 job 파일 생성 헬퍼."""
        job_dir = tmp_jobs_dir / job_id
        job_dir.mkdir(parents=True)
        (job_dir / "job.json").write_text(
            json.dumps({
                "job_id": job_id,
                "sequence": "AGCKNFFWKTFTSC",
                "receptors": ["SSTR2"],
                "config": {},
                "created_at": "2026-05-15T00:00:00Z",
            }),
            encoding="utf-8",
        )
        (job_dir / "status.json").write_text(
            json.dumps({"state": state, "progress": 0.0, "eta_seconds": 1800}),
            encoding="utf-8",
        )

    def test_empty_list(self, client: TestClient, tmp_jobs_dir: Path):
        """job 없음 → {"jobs": []}."""
        resp = client.get("/api/flexpepdock/jobs")
        assert resp.status_code == 200
        assert resp.json() == {"jobs": []}

    def test_list_shows_all_jobs(self, client: TestClient, tmp_jobs_dir: Path):
        """job 2개 등록 → 목록 2개."""
        self._create_job(tmp_jobs_dir, "job-aaa", "queued")
        self._create_job(tmp_jobs_dir, "job-bbb", "done")
        resp = client.get("/api/flexpepdock/jobs")
        assert resp.status_code == 200
        jobs = resp.json()["jobs"]
        assert len(jobs) == 2

    def test_status_filter(self, client: TestClient, tmp_jobs_dir: Path):
        """status=queued 필터 — queued만 반환."""
        self._create_job(tmp_jobs_dir, "job-q1", "queued")
        self._create_job(tmp_jobs_dir, "job-d1", "done")
        resp = client.get("/api/flexpepdock/jobs?status=queued")
        assert resp.status_code == 200
        jobs = resp.json()["jobs"]
        assert all(j["status"] == "queued" for j in jobs)
        assert len(jobs) == 1


# ---------------------------------------------------------------------------
# GET /api/flexpepdock/jobs/{job_id}
# ---------------------------------------------------------------------------


class TestJobGet:
    def test_get_nonexistent_job(self, client: TestClient):
        """존재하지 않는 job → 404."""
        resp = client.get("/api/flexpepdock/jobs/nonexistent-uuid")
        assert resp.status_code == 404

    def test_get_existing_job(self, client: TestClient, tmp_jobs_dir: Path):
        """존재하는 job → 200 + 상태 포함."""
        job_id = "test-job-123"
        job_dir = tmp_jobs_dir / job_id
        job_dir.mkdir()
        (job_dir / "job.json").write_text(
            json.dumps({
                "job_id": job_id,
                "sequence": "AGCKNFFWKTFTSC",
                "receptors": ["SSTR2"],
                "config": {},
                "created_at": "2026-05-15T00:00:00Z",
            }),
            encoding="utf-8",
        )
        (job_dir / "status.json").write_text(
            json.dumps({"state": "queued", "progress": 0.0, "eta_seconds": 1800}),
            encoding="utf-8",
        )

        resp = client.get(f"/api/flexpepdock/jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "queued"
        assert data["sequence"] == "AGCKNFFWKTFTSC"


# ---------------------------------------------------------------------------
# GET /api/flexpepdock/jobs/{job_id}/results
# ---------------------------------------------------------------------------


class TestJobResults:
    def _make_job(self, tmp_jobs_dir: Path, job_id: str, state: str = "done") -> None:
        job_dir = tmp_jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "job.json").write_text(
            json.dumps({
                "job_id": job_id,
                "sequence": "AGCKNFFWKTFTSC",
                "receptors": ["SSTR2"],
                "config": {},
                "created_at": "2026-05-15T00:00:00Z",
            }),
            encoding="utf-8",
        )
        (job_dir / "status.json").write_text(
            json.dumps({"state": state, "progress": 1.0 if state == "done" else 0.5, "eta_seconds": 0}),
            encoding="utf-8",
        )
        if state == "done":
            (job_dir / "result.json").write_text(
                json.dumps({
                    "selectivity_matrix": [
                        {"receptor": "SSTR2", "dG_kcal_mol": -11.5, "interface_score": -68.3, "pass": True},
                    ],
                    "selectivity_index": 3.3,
                    "pdb_paths": [],
                }),
                encoding="utf-8",
            )

    def test_results_not_ready(self, client: TestClient, tmp_jobs_dir: Path):
        """running 상태 → 202."""
        self._make_job(tmp_jobs_dir, "run-job", state="running")
        resp = client.get("/api/flexpepdock/jobs/run-job/results")
        assert resp.status_code == 202

    def test_results_done(self, client: TestClient, tmp_jobs_dir: Path):
        """done 상태 → 200 + selectivity_matrix."""
        self._make_job(tmp_jobs_dir, "done-job", state="done")
        resp = client.get("/api/flexpepdock/jobs/done-job/results")
        assert resp.status_code == 200
        data = resp.json()
        assert "selectivity_matrix" in data
        assert "selectivity_index" in data

    def test_results_404(self, client: TestClient):
        """존재하지 않는 job → 404."""
        resp = client.get("/api/flexpepdock/jobs/ghost-job/results")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/flexpepdock/jobs/{job_id}
# ---------------------------------------------------------------------------


class TestJobDelete:
    def _make_job(self, tmp_jobs_dir: Path, job_id: str, state: str) -> None:
        job_dir = tmp_jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "job.json").write_text(
            json.dumps({
                "job_id": job_id,
                "sequence": "AGCKNFFWKTFTSC",
                "receptors": ["SSTR2"],
                "config": {},
                "created_at": "2026-05-15T00:00:00Z",
            }),
            encoding="utf-8",
        )
        (job_dir / "status.json").write_text(
            json.dumps({"state": state, "progress": 0.0, "eta_seconds": 0}),
            encoding="utf-8",
        )

    def test_delete_queued_job(self, client: TestClient, tmp_jobs_dir: Path):
        """queued job 삭제 → 큐에서 제거 (status=failed)."""
        self._make_job(tmp_jobs_dir, "q-job", "queued")
        resp = client.delete("/api/flexpepdock/jobs/q-job")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "removed_from_queue"

        # status.json 확인
        status_p = tmp_jobs_dir / "q-job" / "status.json"
        status = json.loads(status_p.read_text(encoding="utf-8"))
        assert status["state"] == "failed"

    def test_delete_running_job(self, client: TestClient, tmp_jobs_dir: Path):
        """running job 취소 → cancelling 전환."""
        self._make_job(tmp_jobs_dir, "r-job", "running")
        resp = client.delete("/api/flexpepdock/jobs/r-job")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "cancellation_requested"

        status_p = tmp_jobs_dir / "r-job" / "status.json"
        status = json.loads(status_p.read_text(encoding="utf-8"))
        assert status["state"] == "cancelling"

    def test_delete_done_job_rejected(self, client: TestClient, tmp_jobs_dir: Path):
        """done job 삭제 → 영구 보관 정책 — 400."""
        self._make_job(tmp_jobs_dir, "d-job", "done")
        resp = client.delete("/api/flexpepdock/jobs/d-job")
        assert resp.status_code == 400

    def test_delete_nonexistent_job(self, client: TestClient):
        """존재하지 않는 job → 404."""
        resp = client.delete("/api/flexpepdock/jobs/ghost-id")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Lock 동작 테스트
# ---------------------------------------------------------------------------


class TestLockBehavior:
    def test_stale_lock_auto_reclaim(self, tmp_jobs_dir: Path):
        """stale lock (PID 없음) — acquire_lock이 자동 회수 후 True 반환."""
        from pipeline_local.scripts.flexpepdock_worker import acquire_lock, release_lock

        lock_file = tmp_jobs_dir / ".lock"
        # 존재하지 않는 PID로 lock 파일 생성
        lock_file.write_text(
            json.dumps({"pid": 99999999, "acquired_at": time.time()}),
            encoding="utf-8",
        )

        result = acquire_lock()
        assert result is True
        assert lock_file.exists()

        # PID가 현재 프로세스로 업데이트되어야 함
        data = json.loads(lock_file.read_text(encoding="utf-8"))
        assert data["pid"] == os.getpid()

        release_lock()
        assert not lock_file.exists()

    def test_active_lock_blocks(self, tmp_jobs_dir: Path):
        """현재 PID가 hold 중인 lock — acquire_lock이 False 반환."""
        from pipeline_local.scripts.flexpepdock_worker import acquire_lock, release_lock

        lock_file = tmp_jobs_dir / ".lock"
        # 현재 프로세스 PID로 lock 설정 (이미 hold 중 시뮬레이션)
        lock_file.write_text(
            json.dumps({"pid": os.getpid(), "acquired_at": time.time()}),
            encoding="utf-8",
        )

        result = acquire_lock()
        # 현재 PID가 살아있으므로 false 반환
        assert result is False

        # cleanup
        lock_file.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# ETA 학습 테스트
# ---------------------------------------------------------------------------


class TestEtaLearning:
    def test_default_eta_when_no_history(self, tmp_jobs_dir: Path):
        """이력 없음 → 보수적 기본값 (30min × receptor 수)."""
        from pipeline_local.scripts.flexpepdock_worker import estimate_eta

        eta = estimate_eta(n_receptors=2, nstruct=50)
        assert eta == 2 * 30 * 60  # 3600초

    def test_eta_learned_from_history(self, tmp_jobs_dir: Path):
        """이력 5건 이상 → 평균 기반 ETA."""
        from pipeline_local.scripts.flexpepdock_worker import (
            estimate_eta, save_eta_history, ETA_HISTORY_FILE,
        )

        # 5건 이력 주입: 수용체 1개, nstruct=50, 각 10분
        history = [
            {"job_id": f"j{i}", "n_receptors": 1, "nstruct": 50,
             "elapsed_sec": 600.0, "recorded_at": "2026-05-15T00:00:00Z"}
            for i in range(5)
        ]
        save_eta_history(history)

        # 수용체 2개, nstruct=50 → 예상 1200초
        eta = estimate_eta(n_receptors=2, nstruct=50)
        assert 1100 <= eta <= 1300  # 허용 오차

    def test_eta_nstruct_scaling(self, tmp_jobs_dir: Path):
        """nstruct 100은 nstruct 50의 약 2배 ETA."""
        from pipeline_local.scripts.flexpepdock_worker import (
            estimate_eta, save_eta_history,
        )

        history = [
            {"job_id": f"j{i}", "n_receptors": 1, "nstruct": 50,
             "elapsed_sec": 600.0, "recorded_at": "2026-05-15T00:00:00Z"}
            for i in range(5)
        ]
        save_eta_history(history)

        eta_50 = estimate_eta(n_receptors=1, nstruct=50)
        eta_100 = estimate_eta(n_receptors=1, nstruct=100)
        # nstruct 100은 nstruct 50의 ~2배
        assert abs(eta_100 / eta_50 - 2.0) < 0.5


# ---------------------------------------------------------------------------
# 시퀀스 검증 단위 테스트
# ---------------------------------------------------------------------------


class TestValidateSequence:
    def test_valid_sst14(self):
        from pipeline_local.scripts.flexpepdock_worker import validate_sequence
        ok, err = validate_sequence("AGCKNFFWKTFTSC")
        assert ok is True
        assert err == ""

    def test_wrong_length(self):
        from pipeline_local.scripts.flexpepdock_worker import validate_sequence
        ok, err = validate_sequence("AGCKNFFWKTFTS")  # 13aa
        assert ok is False
        assert "14aa" in err

    def test_invalid_aa(self):
        from pipeline_local.scripts.flexpepdock_worker import validate_sequence
        ok, err = validate_sequence("XGCKNFFWKTFTSC")
        assert ok is False
        assert "아미노산" in err

    def test_missing_cys3(self):
        from pipeline_local.scripts.flexpepdock_worker import validate_sequence
        ok, err = validate_sequence("AGAKNFFWKTFTSC")  # pos2=A
        assert ok is False
        assert "Cys3" in err

    def test_missing_cys14(self):
        from pipeline_local.scripts.flexpepdock_worker import validate_sequence
        ok, err = validate_sequence("AGCKNFFWKTFTSA")  # pos13=A
        assert ok is False
        assert "Cys14" in err
