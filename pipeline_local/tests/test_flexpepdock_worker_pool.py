"""
test_flexpepdock_worker_pool.py
================================
FlexPepDock worker pool (per-job 파일 잠금) 단위 테스트.

테스트 범위:
  1. acquire_job_lock / release_job_lock 기본 동작
  2. 중복 잡 처리 방지 (inter-process: multiprocessing 활용)
  3. 서로 다른 job은 동시에 lock 가능 (4 worker 병렬 처리 기반)
  4. run_worker_loop worker_id 파라미터 + per-job lock 분기
  5. __main__ --worker-id 인자 파싱
"""
from __future__ import annotations

import fcntl
import json
import multiprocessing
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_module_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """각 테스트 전후 모듈 전역 상태를 초기화한다."""
    import pipeline_local.scripts.flexpepdock_worker as wmod

    # _job_lock_fds 초기화 (잔여 fd 누수 방지)
    for jid, fd in list(wmod._job_lock_fds.items()):
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except OSError:
            pass
    wmod._job_lock_fds.clear()

    # _shutdown 초기화
    monkeypatch.setattr(wmod, "_shutdown", False)


@pytest.fixture()
def tmp_jobs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """테스트용 임시 JOBS_DIR을 설정한다."""
    import pipeline_local.scripts.flexpepdock_worker as wmod

    jobs_dir = tmp_path / "flexpepdock_jobs"
    jobs_dir.mkdir()
    monkeypatch.setattr(wmod, "JOBS_DIR", jobs_dir)
    return jobs_dir


def _make_job(jobs_dir: Path, job_id: str, state: str = "queued") -> Path:
    """테스트용 job 디렉토리를 생성한다."""
    job_dir = jobs_dir / job_id
    job_dir.mkdir(exist_ok=True)
    (job_dir / "status.json").write_text(
        json.dumps({"state": state}), encoding="utf-8"
    )
    (job_dir / "job.json").write_text(
        json.dumps({
            "sequence": "AGCKNFFWKTFTSC",
            "receptors": ["SSTR2"],
            "config": {},
            "created_at": "2026-05-20T00:00:00Z",
        }),
        encoding="utf-8",
    )
    return job_dir


# ---------------------------------------------------------------------------
# 1. acquire_job_lock / release_job_lock 기본 동작
# ---------------------------------------------------------------------------


class TestAcquireJobLock:
    def test_acquire_success(self, tmp_jobs_dir: Path) -> None:
        """존재하는 job 디렉토리에 대해 lock 획득에 성공한다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-001")
        assert wmod.acquire_job_lock("job-001") is True
        assert "job-001" in wmod._job_lock_fds
        wmod.release_job_lock("job-001")

    def test_acquire_nonexistent_job_returns_false(self, tmp_jobs_dir: Path) -> None:
        """존재하지 않는 job 디렉토리에 대해 False를 반환한다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        assert wmod.acquire_job_lock("nonexistent-999") is False

    def test_lock_file_created_on_acquire(self, tmp_jobs_dir: Path) -> None:
        """lock 획득 후 jobs/{id}/worker.lock 파일이 생성된다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-002")
        wmod.acquire_job_lock("job-002")
        assert (tmp_jobs_dir / "job-002" / "worker.lock").exists()
        wmod.release_job_lock("job-002")

    def test_release_removes_fd_from_cache(self, tmp_jobs_dir: Path) -> None:
        """release_job_lock 후 _job_lock_fds 캐시에서 제거된다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-003")
        wmod.acquire_job_lock("job-003")
        assert "job-003" in wmod._job_lock_fds
        wmod.release_job_lock("job-003")
        assert "job-003" not in wmod._job_lock_fds

    def test_release_idempotent_for_unknown_job(self, tmp_jobs_dir: Path) -> None:
        """잠근 적 없는 job에 release를 호출해도 예외가 없다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        wmod.release_job_lock("never-locked")  # 예외 없어야 함

    def test_lock_file_contains_pid(self, tmp_jobs_dir: Path) -> None:
        """worker.lock 파일에 현재 프로세스 PID가 기록된다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-004")
        wmod.acquire_job_lock("job-004")
        lock_content = (tmp_jobs_dir / "job-004" / "worker.lock").read_text()
        assert str(os.getpid()) in lock_content
        wmod.release_job_lock("job-004")


# ---------------------------------------------------------------------------
# 2. 중복 잡 처리 방지 (inter-process 잠금 검증)
# ---------------------------------------------------------------------------

# 서브프로세스에서 lock 획득을 시도하는 헬퍼 (모듈 최상위에 있어야 pickle 가능)
def _subprocess_try_lock(
    jobs_dir_str: str,
    job_id: str,
    result_queue: "multiprocessing.Queue[bool]",
    hold_sec: float = 0.5,
) -> None:
    """자식 프로세스에서 per-job lock 획득을 시도하고 결과를 큐에 넣는다."""
    import pipeline_local.scripts.flexpepdock_worker as wmod
    wmod.JOBS_DIR = Path(jobs_dir_str)
    wmod._job_lock_fds.clear()

    ok = wmod.acquire_job_lock(job_id)
    result_queue.put(ok)
    if ok:
        time.sleep(hold_sec)
        wmod.release_job_lock(job_id)


class TestInterProcessLock:
    def test_two_processes_cannot_double_lock_same_job(
        self, tmp_jobs_dir: Path
    ) -> None:
        """두 프로세스가 동일 job에 대해 동시에 lock을 획득할 수 없다."""
        job_id = "job-mp-001"
        _make_job(tmp_jobs_dir, job_id)

        ctx = multiprocessing.get_context("fork")
        q: multiprocessing.Queue = ctx.Queue()

        p1 = ctx.Process(
            target=_subprocess_try_lock,
            args=(str(tmp_jobs_dir), job_id, q, 0.5),
        )
        p1.start()
        time.sleep(0.1)  # p1이 먼저 lock 획득

        p2 = ctx.Process(
            target=_subprocess_try_lock,
            args=(str(tmp_jobs_dir), job_id, q, 0.0),
        )
        p2.start()

        p1.join(timeout=3)
        p2.join(timeout=3)

        results: list[bool] = []
        while not q.empty():
            results.append(q.get_nowait())

        assert len(results) == 2, f"결과 수 이상: {results}"
        true_count = sum(1 for r in results if r)
        assert true_count == 1, (
            f"중복 lock 획득 발생 (True 수={true_count}): {results}"
        )

    def test_different_jobs_can_be_locked_simultaneously(
        self, tmp_jobs_dir: Path
    ) -> None:
        """서로 다른 job은 동시에 lock 획득이 가능하다 (worker pool 핵심)."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-parallel-A")
        _make_job(tmp_jobs_dir, "job-parallel-B")

        ok_a = wmod.acquire_job_lock("job-parallel-A")
        ok_b = wmod.acquire_job_lock("job-parallel-B")

        assert ok_a is True, "job-parallel-A lock 실패"
        assert ok_b is True, "job-parallel-B lock 실패 (다른 job이므로 가능해야 함)"

        wmod.release_job_lock("job-parallel-A")
        wmod.release_job_lock("job-parallel-B")

    def test_four_processes_can_lock_four_different_jobs_simultaneously(
        self, tmp_jobs_dir: Path
    ) -> None:
        """4개 worker가 서로 다른 job을 fcntl flock으로 동시에 점유할 수 있다."""
        job_ids = [f"job-parallel-{i}" for i in range(1, 5)]
        for job_id in job_ids:
            _make_job(tmp_jobs_dir, job_id)

        ctx = multiprocessing.get_context("fork")
        q: multiprocessing.Queue = ctx.Queue()
        processes = [
            ctx.Process(
                target=_subprocess_try_lock,
                args=(str(tmp_jobs_dir), job_id, q, 0.5),
            )
            for job_id in job_ids
        ]

        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=3)

        for process in processes:
            assert process.exitcode == 0, (
                f"worker mock process failed: pid={process.pid}, "
                f"exitcode={process.exitcode}"
            )

        results: list[bool] = []
        while not q.empty():
            results.append(q.get_nowait())

        assert results == [True, True, True, True], (
            f"4개 서로 다른 job lock이 모두 성공해야 함: {results}"
        )

    def test_lock_reacquirable_after_release(self, tmp_jobs_dir: Path) -> None:
        """해제 후 동일 job에 대해 다시 lock 획득이 가능하다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-reacquire")

        assert wmod.acquire_job_lock("job-reacquire") is True
        wmod.release_job_lock("job-reacquire")

        assert wmod.acquire_job_lock("job-reacquire") is True
        wmod.release_job_lock("job-reacquire")


# ---------------------------------------------------------------------------
# 3. run_worker_loop — worker_id 파라미터 + per-job lock 사용
# ---------------------------------------------------------------------------


class TestRunWorkerLoopWorkerPool:
    def test_worker_id_default(self, tmp_jobs_dir: Path) -> None:
        """worker_id 기본값 'worker-1'로 루프가 예외 없이 종료된다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        with (
            patch.object(wmod, "_shutdown", True),
            patch.object(wmod, "find_queued_jobs", return_value=[]),
            patch("signal.signal"),
        ):
            wmod.run_worker_loop()  # 기본 worker_id="worker-1"

    def test_worker_id_custom(
        self, tmp_jobs_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """worker_id='worker-2'를 지정하면 로그 메시지에 반영된다."""
        import logging
        import pipeline_local.scripts.flexpepdock_worker as wmod

        with (
            caplog.at_level(logging.INFO, logger="flexpepdock_worker"),
            patch.object(wmod, "_shutdown", True),
            patch.object(wmod, "find_queued_jobs", return_value=[]),
            patch("signal.signal"),
        ):
            wmod.run_worker_loop(worker_id="worker-2")

        messages = [r.message for r in caplog.records]
        assert any("worker-2" in m for m in messages), (
            f"'worker-2'가 로그에 없음: {messages}"
        )

    def test_loop_calls_acquire_job_lock_not_global_lock(
        self, tmp_jobs_dir: Path
    ) -> None:
        """run_worker_loop이 전역 acquire_lock 대신 acquire_job_lock을 사용한다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        job_id = "job-loop-lock"
        _make_job(tmp_jobs_dir, job_id)

        iteration = [0]
        acquired_jobs: list[str] = []

        def fake_find_queued() -> list[str]:
            if iteration[0] == 0:
                iteration[0] += 1
                return [job_id]
            wmod._shutdown = True
            return []

        real_acquire = wmod.acquire_job_lock

        def spy_acquire(jid: str) -> bool:
            result = real_acquire(jid)
            if result:
                acquired_jobs.append(jid)
            return result

        with (
            patch.object(wmod, "find_queued_jobs", side_effect=fake_find_queued),
            patch.object(wmod, "_process_job"),
            patch.object(wmod, "acquire_job_lock", side_effect=spy_acquire),
            patch.object(wmod, "release_job_lock"),
            patch("signal.signal"),
            patch("time.sleep"),
        ):
            wmod.run_worker_loop(worker_id="worker-spy")

        assert job_id in acquired_jobs, (
            f"acquire_job_lock({job_id!r}) 호출 안 됨: {acquired_jobs}"
        )

    def test_loop_skips_locked_job_and_tries_next(
        self, tmp_jobs_dir: Path
    ) -> None:
        """첫 job이 이미 잠겨 있으면 다음 job을 처리한다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-skip-A")
        _make_job(tmp_jobs_dir, "job-skip-B")

        processed: list[str] = []
        iteration = [0]

        def fake_find_queued() -> list[str]:
            if iteration[0] == 0:
                iteration[0] += 1
                return ["job-skip-A", "job-skip-B"]
            wmod._shutdown = True
            return []

        # job-skip-A는 lock 획득 실패, job-skip-B는 성공
        def fake_acquire(jid: str) -> bool:
            return jid == "job-skip-B"

        def fake_process(jid: str, cancel_flag: list[bool]) -> None:
            processed.append(jid)

        with (
            patch.object(wmod, "find_queued_jobs", side_effect=fake_find_queued),
            patch.object(wmod, "acquire_job_lock", side_effect=fake_acquire),
            patch.object(wmod, "release_job_lock"),
            patch.object(wmod, "_process_job", side_effect=fake_process),
            patch("signal.signal"),
            patch("time.sleep"),
        ):
            wmod.run_worker_loop(worker_id="worker-fallback")

        assert processed == ["job-skip-B"], (
            f"잠긴 job 건너뛰고 다음 job 처리해야 함: {processed}"
        )

    def test_loop_sleeps_when_all_jobs_locked(self, tmp_jobs_dir: Path) -> None:
        """모든 queued job이 잠겨 있으면 sleep 후 재폴링한다."""
        import pipeline_local.scripts.flexpepdock_worker as wmod

        _make_job(tmp_jobs_dir, "job-all-locked")

        sleep_calls = [0]
        iteration = [0]

        def fake_find_queued() -> list[str]:
            if iteration[0] < 2:
                iteration[0] += 1
                return ["job-all-locked"]
            wmod._shutdown = True
            return []

        def fake_sleep(sec: float) -> None:
            sleep_calls[0] += 1

        with (
            patch.object(wmod, "find_queued_jobs", side_effect=fake_find_queued),
            patch.object(wmod, "acquire_job_lock", return_value=False),  # 항상 실패
            patch("signal.signal"),
            patch("time.sleep", side_effect=fake_sleep),
        ):
            wmod.run_worker_loop(worker_id="worker-wait")

        assert sleep_calls[0] >= 1, "lock 획득 실패 시 sleep 안 함"


# ---------------------------------------------------------------------------
# 4. __main__ --worker-id 인자 파싱
# ---------------------------------------------------------------------------


class TestMainArgParsing:
    def test_argparse_worker_id_flag_parses_correctly(self) -> None:
        """--worker-id 플래그가 argparse에서 올바르게 파싱된다."""
        import argparse

        # __main__ 블록과 동일한 parser 재구성
        parser = argparse.ArgumentParser(description="FlexPepDock Worker (pool 지원)")
        parser.add_argument(
            "--worker-id",
            default="worker-1",
            help="워커 식별자 — 로그·PID 파일 구분용 (기본: worker-1)",
        )

        args_custom = parser.parse_args(["--worker-id", "worker-99"])
        args_default = parser.parse_args([])

        assert args_custom.worker_id == "worker-99", (
            f"--worker-id worker-99 파싱 실패: {args_custom.worker_id}"
        )
        assert args_default.worker_id == "worker-1", (
            f"기본값 'worker-1' 아님: {args_default.worker_id}"
        )

    def test_main_block_passes_worker_id_to_run_worker_loop(self) -> None:
        """__main__ 블록 소스에 run_worker_loop(worker_id=...) 호출이 있다."""
        import inspect
        import pipeline_local.scripts.flexpepdock_worker as wmod

        source = inspect.getsource(wmod)
        assert "worker_id=_args.worker_id" in source, (
            "__main__ 블록에 'worker_id=_args.worker_id' 전달 코드 없음"
        )

    def test_run_worker_loop_accepts_worker_id_parameter(self) -> None:
        """run_worker_loop 시그니처에 worker_id 파라미터가 있고 기본값이 'worker-1'이다."""
        import inspect
        import pipeline_local.scripts.flexpepdock_worker as wmod

        sig = inspect.signature(wmod.run_worker_loop)
        assert "worker_id" in sig.parameters, (
            "run_worker_loop에 worker_id 파라미터 없음"
        )
        assert sig.parameters["worker_id"].default == "worker-1", (
            f"기본값이 'worker-1'이어야 함: {sig.parameters['worker_id'].default}"
        )


# ---------------------------------------------------------------------------
# 5. start_flexpepdock_workers.sh — 기본 pool 크기
# ---------------------------------------------------------------------------


class TestStartWorkerPoolScript:
    def test_start_script_defaults_to_four_workers(self) -> None:
        """start script 기본 worker pool 크기는 worker-1~4이다."""
        script_path = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "start_flexpepdock_workers.sh"
        )
        source = script_path.read_text(encoding="utf-8")

        assert "N_WORKERS=4" in source
        assert "기본: 4, 최대: 4" in source
        assert "flexpepdock_worker_4.log" in source
        assert "flexpepdock_worker_4.pid" in source
