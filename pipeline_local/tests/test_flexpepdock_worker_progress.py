"""
test_flexpepdock_worker_progress.py
=====================================
_start_progress_ticker — nstruct 단위 sub-progress 세분화 단위 테스트.

V5-R3: receptor 1개가 1h+ 실행 중일 때 progress=0.0%로 멈춰 보이는 문제 해결.
검증 항목:
  1. ticker가 write_status를 호출하는지
  2. progress 값이 (receptor_idx + sub_progress) / total 공식을 따르는지
  3. sub_progress가 0.95 이하로 cap되는지
  4. stop_event.set() 후 스레드가 안전하게 종료되는지
  5. eta_per_receptor_sec=0 에서 ZeroDivisionError 없이 동작하는지
  6. 복수 ticker 동시 실행이 간섭 없이 작동하는지

[주의] mock.patch.object 를 context manager(with)로 쓰면 with 블록 탈출 시
mock이 해제되어 daemon 스레드에서 원본 write_status 가 호출된다.
→ patcher.start() / patcher.stop() 패턴을 사용한다.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

# 프로젝트 루트 → import 경로 설정
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

import importlib.util

_WORKER_PATH = _REPO_ROOT / "pipeline_local" / "scripts" / "flexpepdock_worker.py"
assert _WORKER_PATH.exists(), f"flexpepdock_worker.py 없음: {_WORKER_PATH}"

_spec = importlib.util.spec_from_file_location("flexpepdock_worker", _WORKER_PATH)
_worker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_worker)  # type: ignore[union-attr]

_start_progress_ticker = _worker._start_progress_ticker


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _run_ticker(
    *,
    receptor_idx: int = 0,
    total_receptors: int = 5,
    job_start: float | None = None,
    job_eta_sec: int = 3600,
    eta_per_receptor_sec: float = 720.0,
    interval_sec: float = 0.05,
    sleep_sec: float = 0.25,
    job_id: str | None = None,
) -> list[dict[str, Any]]:
    """ticker를 시작하고 sleep_sec 대기 후 stop.

    write_status kwargs 목록을 반환한다.

    [중요] patcher.start()/stop()을 사용하여 daemon 스레드가 mock 활성 상태에서 호출되도록 보장.
    """
    captured: list[dict[str, Any]] = []
    job_start_val = job_start if job_start is not None else time.monotonic()
    jid = job_id or f"test-job-{receptor_idx}"

    # patcher.start() / stop() — with 블록 외부에서 mock 유지
    patcher = mock.patch.object(
        _worker,
        "write_status",
        side_effect=lambda *args, **kw: captured.append(kw),
    )
    patcher.start()
    try:
        stop = _start_progress_ticker(
            job_id=jid,
            receptor_idx=receptor_idx,
            total_receptors=total_receptors,
            job_start=job_start_val,
            job_eta_sec=job_eta_sec,
            eta_per_receptor_sec=eta_per_receptor_sec,
            started_at="2026-05-20T00:00:00Z",
            interval_sec=interval_sec,
        )
        time.sleep(sleep_sec)
        stop.set()
        time.sleep(0.05)  # 마지막 tick race condition 마진
    finally:
        patcher.stop()

    return captured


# ---------------------------------------------------------------------------
# 테스트 케이스
# ---------------------------------------------------------------------------


class TestProgressTickerBasic:
    """기본 동작 검증."""

    def test_ticker_calls_write_status(self) -> None:
        """ticker가 interval 후 write_status를 최소 1회 호출해야 한다."""
        captured = _run_ticker(interval_sec=0.05, sleep_sec=0.25)
        assert len(captured) >= 1, "write_status가 한 번도 호출되지 않음"

    def test_progress_formula(self) -> None:
        """progress = (receptor_idx + sub_progress) / total 공식 준수."""
        receptor_idx = 2
        total = 5
        captured = _run_ticker(
            receptor_idx=receptor_idx,
            total_receptors=total,
            interval_sec=0.05,
            sleep_sec=0.25,
        )
        assert captured, "write_status 호출 없음"
        for call in captured:
            p = call["progress"]
            lower = receptor_idx / total
            upper = (receptor_idx + 1) / total
            assert lower <= p < upper, (
                f"progress={p:.4f} 이 [{lower:.4f}, {upper:.4f}) 범위를 벗어남"
            )

    def test_sub_progress_capped_at_0_95(self) -> None:
        """매우 짧은 ETA 대비 긴 elapsed → sub_progress <= 0.95 cap."""
        receptor_idx = 0
        total = 1
        # 이미 1000초 경과 시뮬레이션 (job_start를 1000초 전으로 설정)
        job_start = time.monotonic() - 1000.0
        captured = _run_ticker(
            receptor_idx=receptor_idx,
            total_receptors=total,
            job_start=job_start,
            job_eta_sec=100,
            eta_per_receptor_sec=1.0,  # ETA=1초인데 이미 훨씬 더 경과
            interval_sec=0.05,
            sleep_sec=0.25,
        )
        assert captured, "write_status 호출 없음"
        for call in captured:
            assert call["progress"] <= 0.95 + 1e-9, (
                f"sub_progress cap 0.95 초과: progress={call['progress']}"
            )

    def test_state_is_running(self) -> None:
        """ticker가 기록하는 state는 항상 'running' 이어야 한다."""
        captured = _run_ticker(
            receptor_idx=1,
            total_receptors=3,
            interval_sec=0.05,
            sleep_sec=0.25,
        )
        assert captured, "write_status 호출 없음"
        for call in captured:
            assert call["state"] == "running", f"state={call['state']} (expected 'running')"


class TestProgressTickerEdgeCases:
    """엣지 케이스 및 안전성 검증."""

    def test_zero_eta_per_receptor_no_divzero(self) -> None:
        """eta_per_receptor_sec=0 → ZeroDivisionError 없이 sub_progress=0.0."""
        captured = _run_ticker(
            receptor_idx=0,
            total_receptors=5,
            eta_per_receptor_sec=0.0,
            interval_sec=0.05,
            sleep_sec=0.25,
        )
        # 예외 없이 실행되어야 하고, progress는 receptor_idx/total = 0.0
        for call in captured:
            assert call["progress"] == pytest.approx(0.0, abs=1e-6), (
                f"zero ETA에서 progress={call['progress']} != 0.0"
            )

    def test_stop_event_terminates_thread(self) -> None:
        """stop_event.set() 후 추가 호출이 최대 1회 이하여야 한다."""
        captured: list[dict[str, Any]] = []
        job_start = time.monotonic()

        patcher = mock.patch.object(
            _worker,
            "write_status",
            side_effect=lambda *args, **kw: captured.append(kw),
        )
        patcher.start()
        try:
            stop = _start_progress_ticker(
                job_id="test-stop",
                receptor_idx=0,
                total_receptors=5,
                job_start=job_start,
                job_eta_sec=3600,
                eta_per_receptor_sec=720.0,
                started_at="2026-05-20T00:00:00Z",
                interval_sec=0.05,
            )
            time.sleep(0.15)
            count_before = len(captured)
            stop.set()
            time.sleep(0.2)  # stop 후 대기
            count_after = len(captured)
        finally:
            patcher.stop()

        assert count_after - count_before <= 1, (
            f"stop.set() 후 {count_after - count_before}회 추가 호출됨 (최대 1 허용)"
        )

    def test_remaining_eta_non_negative(self) -> None:
        """잔여 ETA 는 항상 0 이상이어야 한다."""
        # 이미 ETA를 훨씬 초과한 상황 시뮬레이션
        job_start = time.monotonic() - 9999.0
        captured = _run_ticker(
            receptor_idx=0,
            total_receptors=5,
            job_start=job_start,
            job_eta_sec=100,
            eta_per_receptor_sec=20.0,
            interval_sec=0.05,
            sleep_sec=0.2,
        )
        for call in captured:
            assert call["eta_seconds"] >= 0, (
                f"eta_seconds={call['eta_seconds']} 음수"
            )

    def test_two_tickers_concurrent(self) -> None:
        """두 ticker가 동시 실행되어도 각각 독립적으로 동작한다.

        단일 patcher로 모든 호출을 캡처하고 job_id로 구분한다.
        (두 ticker가 같은 _worker.write_status를 공유하므로 별도 patcher 불가)
        """
        # (job_id, kwargs) 튜플로 캡처
        captured: list[tuple[str, dict[str, Any]]] = []

        def _side_effect(*args: Any, **kw: Any) -> None:
            # write_status(job_id, state=...) — job_id는 첫 번째 positional arg
            jid = args[0] if args else ""
            captured.append((jid, kw))

        job_start = time.monotonic()

        patcher = mock.patch.object(_worker, "write_status", side_effect=_side_effect)
        patcher.start()
        try:
            stop0 = _start_progress_ticker(
                job_id="test-concurrent-0",
                receptor_idx=0,
                total_receptors=5,
                job_start=job_start,
                job_eta_sec=3600,
                eta_per_receptor_sec=720.0,
                started_at="2026-05-20T00:00:00Z",
                interval_sec=0.06,
            )
            stop1 = _start_progress_ticker(
                job_id="test-concurrent-1",
                receptor_idx=1,
                total_receptors=5,
                job_start=job_start,
                job_eta_sec=3600,
                eta_per_receptor_sec=720.0,
                started_at="2026-05-20T00:00:00Z",
                interval_sec=0.06,
            )
            time.sleep(0.3)
            stop0.set()
            stop1.set()
            time.sleep(0.05)
        finally:
            patcher.stop()

        calls_0 = [kw for jid, kw in captured if jid == "test-concurrent-0"]
        calls_1 = [kw for jid, kw in captured if jid == "test-concurrent-1"]

        assert len(calls_0) >= 1, "ticker-0 호출 없음"
        assert len(calls_1) >= 1, "ticker-1 호출 없음"

        # ticker-1의 progress는 [1/5, 2/5) 범위여야 함
        for kw in calls_1:
            assert 1 / 5 - 1e-9 <= kw["progress"] < 2 / 5 + 1e-9, (
                f"ticker-1 progress={kw['progress']:.4f} 범위 벗어남"
            )

    def test_daemon_thread_does_not_block_exit(self) -> None:
        """ticker 스레드가 daemon=True 여서 메인 종료를 막지 않음을 확인."""
        job_start = time.monotonic()

        patcher = mock.patch.object(_worker, "write_status")
        patcher.start()
        try:
            stop = _start_progress_ticker(
                job_id="test-daemon",
                receptor_idx=0,
                total_receptors=3,
                job_start=job_start,
                job_eta_sec=1800,
                eta_per_receptor_sec=600.0,
                started_at="2026-05-20T00:00:00Z",
                interval_sec=100.0,  # 실제로는 거의 tick 안 함
            )
        finally:
            patcher.stop()

        # ticker thread 탐색 — daemon 이어야 함
        ticker_threads = [
            t for t in threading.enumerate()
            if "progress-ticker-test-daemon" in t.name
        ]
        for t in ticker_threads:
            assert t.daemon, f"스레드 {t.name} 가 daemon=False"

        stop.set()


class TestProgressFormulaUnit:
    """수식 단위 검증 — ticker 없이 공식만 검증."""

    @pytest.mark.parametrize("receptor_idx,total,elapsed,eta_per_r,expected_min,expected_max", [
        (0, 5, 0.0, 720.0, 0.0, 0.2),          # 시작 직후: 0.0/5
        (1, 5, 360.0, 720.0, 0.2, 0.4),         # 50% 진행: [1/5, 2/5)
        (4, 5, 720.0, 720.0, 0.8, 1.0),          # 마지막 receptor
        (0, 1, 9999.0, 1.0, 0.0, 0.95001),       # 단일 receptor, ETA 초과 → cap 0.95
    ])
    def test_progress_range(
        self,
        receptor_idx: int,
        total: int,
        elapsed: float,
        eta_per_r: float,
        expected_min: float,
        expected_max: float,
    ) -> None:
        """progress 계산이 예상 범위 안에 있는지 확인."""
        if eta_per_r > 0:
            sub_progress = min(0.95, elapsed / eta_per_r)
        else:
            sub_progress = 0.0
        progress = (receptor_idx + sub_progress) / total
        assert expected_min <= progress <= expected_max, (
            f"receptor={receptor_idx}/{total}, elapsed={elapsed}s → "
            f"progress={progress:.4f} ∉ [{expected_min}, {expected_max}]"
        )

    def test_first_receptor_initial_progress_is_zero(self) -> None:
        """첫 번째 receptor 시작 직전의 progress는 0.0 이어야 한다 (elapsed=0)."""
        sub_progress = min(0.95, 0.0 / 720.0)  # elapsed=0
        progress = (0 + sub_progress) / 5
        assert progress == pytest.approx(0.0)

    def test_cap_prevents_false_completion(self) -> None:
        """elapsed >> ETA 여도 progress < (receptor_idx+1)/total 유지."""
        receptor_idx = 2
        total = 5
        # elapsed = 9999, eta_per_r = 1 → sub_progress = 0.95 (cap)
        sub_progress = min(0.95, 9999.0 / 1.0)
        progress = (receptor_idx + sub_progress) / total
        # (2 + 0.95) / 5 = 0.59, 상한은 (2+1)/5 = 0.6
        assert progress < (receptor_idx + 1) / total
