"""
test_orphan_worker_cleanup.py
==============================
cleanup_stale_worker_pid_files() 및 _cleanup_stale_lock_if_dead() 단위 테스트.

테스트 전략:
- 실제 /tmp 파일을 쓰지 않음 — tmp_path fixture(pytest) + monkeypatch로 격리
- os.kill 은 모킹하여 PID alive/dead 시나리오를 제어
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# 헬퍼: flexpepdock_worker 를 격리 경로로 import
# ---------------------------------------------------------------------------

import importlib
import sys


def _import_worker_module(tmp_path: Path, monkeypatch: Any):
    """
    flexpepdock_worker 모듈을 임포트하면서 경로 상수를 tmp_path 기준으로
    패치한다.  모듈을 두 번 이상 임포트해도 패치가 유효하도록 reload 한다.
    """
    # 이미 임포트되어 있으면 제거하여 상수 패치가 반영되도록 한다.
    sys.modules.pop("pipeline_local.scripts.flexpepdock_worker", None)

    import pipeline_local.scripts.flexpepdock_worker as wmod

    # _PID_FILE_DIR, LOCK_FILE 을 tmp_path 기준으로 교체
    monkeypatch.setattr(wmod, "_PID_FILE_DIR", tmp_path)
    monkeypatch.setattr(wmod, "LOCK_FILE", tmp_path / ".lock")
    monkeypatch.setattr(wmod, "_MAX_WORKER_SLOTS", 4)

    return wmod


# ---------------------------------------------------------------------------
# 기본 픽스처: 각 테스트마다 격리된 tmp_path 사용
# ---------------------------------------------------------------------------

@pytest.fixture()
def wmod(tmp_path: Path, monkeypatch: Any):
    return _import_worker_module(tmp_path, monkeypatch)


# ---------------------------------------------------------------------------
# _pid_alive 관련 테스트
# ---------------------------------------------------------------------------

class TestPidAlive:
    def test_alive_pid(self, wmod):
        """현재 프로세스 PID는 alive 이어야 한다."""
        assert wmod._pid_alive(os.getpid()) is True

    def test_dead_pid(self, wmod):
        """존재하지 않는 PID(999999999)는 dead 이어야 한다."""
        assert wmod._pid_alive(999_999_999) is False


# ---------------------------------------------------------------------------
# cleanup_stale_worker_pid_files 핵심 시나리오
# ---------------------------------------------------------------------------

class TestCleanupStalePidFiles:
    def _write_pid_file(self, tmp_path: Path, slot: int, pid: int) -> Path:
        p = tmp_path / f"flexpepdock_worker_{slot}.pid"
        p.write_text(str(pid), encoding="utf-8")
        return p

    def test_no_pid_files(self, wmod, tmp_path):
        """PID 파일이 하나도 없으면 빈 리스트를 반환한다."""
        cleaned = wmod.cleanup_stale_worker_pid_files()
        assert cleaned == []

    def test_all_dead_pids_are_cleaned(self, wmod, tmp_path):
        """dead PID 파일 3개가 모두 정리되어야 한다."""
        dead_pid = 999_999_998
        for slot in (1, 2, 3):
            self._write_pid_file(tmp_path, slot, dead_pid)

        with patch.object(wmod, "_pid_alive", return_value=False):
            cleaned = wmod.cleanup_stale_worker_pid_files()

        assert set(cleaned) == {dead_pid}
        assert len(cleaned) == 3
        # 파일이 삭제되었는지 확인
        for slot in (1, 2, 3):
            assert not (tmp_path / f"flexpepdock_worker_{slot}.pid").exists()

    def test_alive_pid_is_kept(self, wmod, tmp_path):
        """alive PID 파일은 건드리지 않아야 한다."""
        alive_pid = os.getpid()
        pid_path = self._write_pid_file(tmp_path, 1, alive_pid)

        cleaned = wmod.cleanup_stale_worker_pid_files()

        assert cleaned == []
        assert pid_path.exists()

    def test_mixed_alive_and_dead(self, wmod, tmp_path):
        """alive 1개 + dead 1개 → dead만 정리."""
        alive_pid = os.getpid()
        dead_pid = 999_999_997

        self._write_pid_file(tmp_path, 1, alive_pid)
        self._write_pid_file(tmp_path, 2, dead_pid)

        def _mock_alive(pid: int) -> bool:
            return pid == alive_pid

        with patch.object(wmod, "_pid_alive", side_effect=_mock_alive):
            cleaned = wmod.cleanup_stale_worker_pid_files()

        assert cleaned == [dead_pid]
        assert (tmp_path / "flexpepdock_worker_1.pid").exists()
        assert not (tmp_path / "flexpepdock_worker_2.pid").exists()

    def test_corrupt_pid_file_is_removed(self, wmod, tmp_path):
        """PID 파일 내용이 숫자가 아니면 파일을 삭제하고 cleaned에 포함하지 않는다."""
        corrupt = tmp_path / "flexpepdock_worker_1.pid"
        corrupt.write_text("not_a_number", encoding="utf-8")

        cleaned = wmod.cleanup_stale_worker_pid_files()

        assert cleaned == []
        assert not corrupt.exists()

    def test_slot_range_respected(self, wmod, tmp_path, monkeypatch):
        """_MAX_WORKER_SLOTS=2 이면 slot 3,4 는 검사하지 않는다."""
        monkeypatch.setattr(wmod, "_MAX_WORKER_SLOTS", 2)
        dead_pid = 999_999_996
        # slot 3 에 dead PID 파일을 만들어 두되, 검사하지 않으면 파일이 남아야 함
        stray = self._write_pid_file(tmp_path, 3, dead_pid)

        with patch.object(wmod, "_pid_alive", return_value=False):
            cleaned = wmod.cleanup_stale_worker_pid_files()

        # slot 3 은 범위 밖이므로 정리되지 않음
        assert cleaned == []
        assert stray.exists()


# ---------------------------------------------------------------------------
# _cleanup_stale_lock_if_dead
# ---------------------------------------------------------------------------

class TestCleanupStaleLock:
    def _write_lock(self, tmp_path: Path, pid: int) -> Path:
        lock = tmp_path / ".lock"
        lock.write_text(json.dumps({"pid": pid, "acquired_at": 0.0}), encoding="utf-8")
        return lock

    def test_no_lock_file(self, wmod, tmp_path):
        """lock 파일 없으면 아무것도 하지 않는다."""
        wmod._cleanup_stale_lock_if_dead()  # should not raise

    def test_dead_lock_is_removed(self, wmod, tmp_path):
        """dead PID가 보유한 lock 파일은 삭제되어야 한다."""
        lock = self._write_lock(tmp_path, 999_999_995)

        with patch.object(wmod, "_pid_alive", return_value=False):
            wmod._cleanup_stale_lock_if_dead()

        assert not lock.exists()

    def test_alive_lock_is_kept(self, wmod, tmp_path):
        """alive PID가 보유한 lock 파일은 보존되어야 한다."""
        lock = self._write_lock(tmp_path, os.getpid())

        wmod._cleanup_stale_lock_if_dead()

        assert lock.exists()

    def test_corrupt_lock_is_removed(self, wmod, tmp_path):
        """JSON 파싱 실패한 lock은 dead로 간주해 삭제한다."""
        lock = tmp_path / ".lock"
        lock.write_text("INVALID_JSON", encoding="utf-8")

        # pid=0 이므로 _pid_alive(0) 호출 — 여기서 False 반환 예상
        with patch.object(wmod, "_pid_alive", return_value=False):
            wmod._cleanup_stale_lock_if_dead()

        assert not lock.exists()


# ---------------------------------------------------------------------------
# 통합: cleanup_stale_worker_pid_files 가 내부적으로 lock도 정리
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_pid_and_lock_both_cleaned(self, wmod, tmp_path):
        """dead worker PID 파일과 dead lock 이 동시에 정리된다."""
        dead_pid = 999_999_994

        pid_file = tmp_path / "flexpepdock_worker_1.pid"
        pid_file.write_text(str(dead_pid), encoding="utf-8")

        lock_file = tmp_path / ".lock"
        lock_file.write_text(
            json.dumps({"pid": dead_pid, "acquired_at": 0.0}), encoding="utf-8"
        )

        with patch.object(wmod, "_pid_alive", return_value=False):
            cleaned = wmod.cleanup_stale_worker_pid_files()

        assert cleaned == [dead_pid]
        assert not pid_file.exists()
        assert not lock_file.exists()
