"""
backend/tests/test_experiment_router.py
========================================
P09 패치 검증: start_experiment 3-way 폴백 (요청값 → runtime_settings → DEFAULT_EXPERIMENT_CONFIG)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from threading import Lock
from typing import Optional
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers — experiment router에서 3-way 폴백 로직만 추출해 검증
# ---------------------------------------------------------------------------


def _resolve_fallback(
    config: dict,
    runtime_settings: dict,
    default: dict,
) -> tuple[int, int, int]:
    """실제 experiment.py 핸들러의 3-way 폴백과 동일한 로직."""
    max_iterations = (
        config.get("max_iterations")
        or runtime_settings.get("max_iterations")
        or default["max_iterations"]
    )
    n_candidates = (
        config.get("n_candidates")
        or runtime_settings.get("n_candidates")
        or default["n_candidates"]
    )
    top_k = (
        config.get("top_k")
        or runtime_settings.get("top_k")
        or default["top_k"]
    )
    return int(max_iterations), int(n_candidates), int(top_k)


# ---------------------------------------------------------------------------
# 테스트 케이스
# ---------------------------------------------------------------------------


class TestExperimentFallback(unittest.TestCase):
    DEFAULT = {"max_iterations": 5, "n_candidates": 8, "top_k": 5}

    # ── 요청값 우선 ──────────────────────────────────────────────────────────

    def test_request_value_takes_priority(self) -> None:
        """요청에 값이 있으면 runtime_settings·default 무시."""
        cfg = {"max_iterations": 10, "n_candidates": 12, "top_k": 7}
        runtime = {"max_iterations": 3, "n_candidates": 3, "top_k": 3}
        mi, nc, tk = _resolve_fallback(cfg, runtime, self.DEFAULT)
        self.assertEqual(mi, 10)
        self.assertEqual(nc, 12)
        self.assertEqual(tk, 7)

    # ── runtime_settings 2순위 ───────────────────────────────────────────────

    def test_runtime_settings_used_when_request_empty(self) -> None:
        """요청값 없을 때 runtime_settings 값을 사용해야 한다."""
        cfg: dict = {}
        runtime = {"max_iterations": 20, "n_candidates": 15, "top_k": 9}
        mi, nc, tk = _resolve_fallback(cfg, runtime, self.DEFAULT)
        self.assertEqual(mi, 20)
        self.assertEqual(nc, 15)
        self.assertEqual(tk, 9)

    def test_runtime_settings_partial(self) -> None:
        """요청값이 일부만 있을 때 나머지는 runtime_settings에서."""
        cfg = {"max_iterations": 7}
        runtime = {"max_iterations": 20, "n_candidates": 15, "top_k": 9}
        mi, nc, tk = _resolve_fallback(cfg, runtime, self.DEFAULT)
        self.assertEqual(mi, 7)   # 요청값 우선
        self.assertEqual(nc, 15)  # runtime_settings
        self.assertEqual(tk, 9)   # runtime_settings

    # ── DEFAULT 3순위 ────────────────────────────────────────────────────────

    def test_default_used_when_all_empty(self) -> None:
        """요청·runtime 모두 없을 때 DEFAULT 사용."""
        cfg: dict = {}
        runtime: dict = {}
        mi, nc, tk = _resolve_fallback(cfg, runtime, self.DEFAULT)
        self.assertEqual(mi, 5)
        self.assertEqual(nc, 8)
        self.assertEqual(tk, 5)

    def test_zero_treated_as_falsy_falls_back(self) -> None:
        """0은 falsy이므로 폴백 동작 확인 (or 연산 특성)."""
        cfg = {"max_iterations": 0}
        runtime = {"max_iterations": 3}
        mi, _, _ = _resolve_fallback(cfg, runtime, self.DEFAULT)
        # 0 → falsy → runtime_settings 값 사용
        self.assertEqual(mi, 3)

    # ── 통합: start_experiment 핸들러 mock 테스트 ────────────────────────────

    def test_start_experiment_uses_runtime_settings_via_mock(self) -> None:
        """
        start_experiment 핸들러가 runtime_settings에서 값을 꺼내
        subprocess.Popen 명령에 포함하는지 mock으로 검증.
        """
        import backend.state as state_mod

        # runtime_settings를 오버라이드
        original_settings = state_mod.runtime_settings.copy()
        original_proc = state_mod.experiment_proc
        original_run_id = state_mod.experiment_run_id

        try:
            state_mod.runtime_settings = {
                "max_iterations": 42,
                "n_candidates": 7,
                "top_k": 3,
            }
            state_mod.experiment_proc = None
            state_mod.experiment_run_id = None

            captured_cmd: list[str] = []

            fake_proc = MagicMock()
            fake_proc.pid = 12345

            def fake_popen(cmd: list[str], **kwargs: object) -> MagicMock:
                captured_cmd.extend(cmd)
                return fake_proc

            with patch("subprocess.Popen", side_effect=fake_popen), \
                 patch("threading.Thread") as mock_thread:
                mock_thread.return_value.start = MagicMock()
                from backend.routers.experiment import start_experiment
                result = start_experiment(config={})

            # 커맨드에 runtime_settings 값이 반영됐는지 확인
            self.assertIn("--max-iterations", captured_cmd)
            idx_mi = captured_cmd.index("--max-iterations")
            self.assertEqual(captured_cmd[idx_mi + 1], "42")

            self.assertIn("--n-candidates", captured_cmd)
            idx_nc = captured_cmd.index("--n-candidates")
            self.assertEqual(captured_cmd[idx_nc + 1], "7")

            self.assertIn("--top-k", captured_cmd)
            idx_tk = captured_cmd.index("--top-k")
            self.assertEqual(captured_cmd[idx_tk + 1], "3")

        finally:
            state_mod.runtime_settings = original_settings
            state_mod.experiment_proc = original_proc
            state_mod.experiment_run_id = original_run_id

    def test_start_experiment_writes_initializing_status_file(self) -> None:
        """P02: Popen 직후 initializing status 파일이 즉시 생성되어야 한다."""
        import backend.state as state_mod

        original_settings = state_mod.runtime_settings.copy()
        original_proc = state_mod.experiment_proc
        original_run_id = state_mod.experiment_run_id
        original_status_file = state_mod.STATUS_FILE
        original_log_file = getattr(state_mod, "_experiment_log_file", None)

        try:
            with TemporaryDirectory() as tmpdir:
                state_mod.runtime_settings = {
                    "max_iterations": 11,
                    "n_candidates": 7,
                    "top_k": 3,
                }
                state_mod.experiment_proc = None
                state_mod.experiment_run_id = None
                state_mod.STATUS_FILE = Path(tmpdir) / "status.json"

                fake_proc = MagicMock()
                fake_proc.pid = 12345

                with patch("subprocess.Popen", return_value=fake_proc), \
                     patch("threading.Thread") as mock_thread:
                    mock_thread.return_value.start = MagicMock()
                    from backend.routers.experiment import start_experiment
                    result = start_experiment(config={})

                status_payload = json.loads(state_mod.STATUS_FILE.read_text(encoding="utf-8"))
                self.assertEqual(status_payload["run_id"], result["run_id"])
                self.assertEqual(status_payload["phase"], "initializing")
                self.assertEqual(status_payload["iteration"], 0)
                self.assertEqual(status_payload["total_iterations"], 11)
                self.assertFalse(status_payload["completed"])
                self.assertTrue(status_payload["connected"])
                self.assertEqual(status_payload["candidates"], [])
                self.assertIn("started_at", status_payload)
        finally:
            if getattr(state_mod, "_experiment_log_file", None) is not None:
                state_mod._experiment_log_file.close()
            state_mod._experiment_log_file = original_log_file
            state_mod.STATUS_FILE = original_status_file
            state_mod.runtime_settings = original_settings
            state_mod.experiment_proc = original_proc
            state_mod.experiment_run_id = original_run_id


class TestReadStatusRuntimeFields(unittest.TestCase):
    """P03: read_status() 후처리 — is_active_run / server_time 주입 검증."""

    # ------------------------------------------------------------------
    # 공통 헬퍼
    # ------------------------------------------------------------------
    def _setup_status_file(
        self,
        state_mod: object,
        tmpdir: str,
        payload: dict,
    ) -> None:
        """임시 상태 파일 작성 + 캐시 초기화."""
        import backend.state as _state
        _state.STATUS_FILE = Path(tmpdir) / "status.json"
        _state.STATUS_FILE.write_text(json.dumps(payload), encoding="utf-8")
        _state._cache = {}
        _state._cache_mtime = 0.0

    def _save_state(self, state_mod: object) -> dict:
        import backend.state as _state
        return {
            "STATUS_FILE": _state.STATUS_FILE,
            "_cache": _state._cache,
            "_cache_mtime": _state._cache_mtime,
        }

    def _restore_state(self, state_mod: object, saved: dict) -> None:
        import backend.state as _state
        _state.STATUS_FILE = saved["STATUS_FILE"]
        _state._cache = saved["_cache"]
        _state._cache_mtime = saved["_cache_mtime"]

    # ------------------------------------------------------------------
    # 기존 케이스 (보강)
    # ------------------------------------------------------------------

    def test_read_status_adds_runtime_fields_for_active_run(self) -> None:
        """P03: completed=False + candidates 존재 → is_active_run=True + server_time."""
        import backend.state as state_mod

        saved = self._save_state(state_mod)
        try:
            with TemporaryDirectory() as tmpdir:
                self._setup_status_file(
                    state_mod, tmpdir,
                    {"run_id": "run-1", "completed": False, "candidates": [{"id": "c1"}]},
                )
                status = state_mod.read_status()

                self.assertTrue(status["is_active_run"])
                self.assertEqual(status["run_id"], "run-1")
                self.assertIn("server_time", status)
        finally:
            self._restore_state(state_mod, saved)

    def test_read_status_marks_missing_status_file_inactive(self) -> None:
        """상태 파일이 없을 때는 inactive + server_time을 반환해야 한다."""
        import backend.state as state_mod

        saved = self._save_state(state_mod)
        try:
            with TemporaryDirectory() as tmpdir:
                import backend.state as _state
                _state.STATUS_FILE = Path(tmpdir) / "missing.json"
                _state._cache = {}
                _state._cache_mtime = 0.0

                status = state_mod.read_status()

                self.assertEqual(status["error"], "no_status_file")
                self.assertFalse(status["connected"])
                self.assertFalse(status["is_active_run"])
                self.assertIn("server_time", status)
        finally:
            self._restore_state(state_mod, saved)

    # ------------------------------------------------------------------
    # P03 신규 케이스
    # ------------------------------------------------------------------

    def test_completed_true_yields_inactive(self) -> None:
        """completed=True 이면 is_active_run=False 이어야 한다."""
        import backend.state as state_mod

        saved = self._save_state(state_mod)
        try:
            with TemporaryDirectory() as tmpdir:
                self._setup_status_file(
                    state_mod, tmpdir,
                    {
                        "run_id": "run-done",
                        "completed": True,
                        "candidates": [{"id": "c1"}],
                        "steps": ["step1"],
                    },
                )
                status = state_mod.read_status()

                self.assertFalse(status["is_active_run"])
                self.assertIn("server_time", status)
        finally:
            self._restore_state(state_mod, saved)

    def test_completed_false_with_steps_yields_active(self) -> None:
        """completed=False + steps 존재 → is_active_run=True."""
        import backend.state as state_mod

        saved = self._save_state(state_mod)
        try:
            with TemporaryDirectory() as tmpdir:
                self._setup_status_file(
                    state_mod, tmpdir,
                    {"run_id": "run-2", "completed": False, "steps": ["step1"]},
                )
                status = state_mod.read_status()

                self.assertTrue(status["is_active_run"])
                self.assertIn("server_time", status)
        finally:
            self._restore_state(state_mod, saved)

    def test_completed_false_no_steps_no_candidates_yields_inactive(self) -> None:
        """completed=False 이어도 steps/candidates 가 없으면 is_active_run=False."""
        import backend.state as state_mod

        saved = self._save_state(state_mod)
        try:
            with TemporaryDirectory() as tmpdir:
                self._setup_status_file(
                    state_mod, tmpdir,
                    {"run_id": "run-3", "completed": False},
                )
                status = state_mod.read_status()

                self.assertFalse(status["is_active_run"])
                self.assertIn("server_time", status)
        finally:
            self._restore_state(state_mod, saved)

    def test_server_time_refreshed_on_cache_hit(self) -> None:
        """캐시 hit 시에도 server_time은 항상 현재 시각으로 갱신되어야 한다."""
        import time
        import backend.state as state_mod

        saved = self._save_state(state_mod)
        try:
            with TemporaryDirectory() as tmpdir:
                self._setup_status_file(
                    state_mod, tmpdir,
                    {"run_id": "run-c", "completed": False, "candidates": [{"id": "c1"}]},
                )

                # 첫 번째 호출 — 캐시 미스, 파일 읽기
                first = state_mod.read_status()
                first_time = first["server_time"]

                # 파일 mtime 변경 없이 잠깐 대기 후 두 번째 호출 → 캐시 hit
                time.sleep(0.05)
                second = state_mod.read_status()
                second_time = second["server_time"]

                # server_time은 두 호출 간에 달라야 한다 (캐시 hit 후 갱신)
                self.assertNotEqual(first_time, second_time)
                self.assertIn("is_active_run", second)
        finally:
            self._restore_state(state_mod, saved)

    def test_error_case_includes_runtime_fields(self) -> None:
        """error/disconnected 케이스도 is_active_run=False + server_time 포함."""
        import backend.state as state_mod

        saved = self._save_state(state_mod)
        try:
            with TemporaryDirectory() as tmpdir:
                import backend.state as _state
                # 파일 없음 → {"error": "no_status_file", "connected": False}
                _state.STATUS_FILE = Path(tmpdir) / "nonexistent.json"
                _state._cache = {}
                _state._cache_mtime = 0.0

                status = state_mod.read_status()

                self.assertFalse(status["is_active_run"])
                self.assertIn("server_time", status)
                self.assertEqual(status.get("error"), "no_status_file")
        finally:
            self._restore_state(state_mod, saved)


if __name__ == "__main__":
    unittest.main()
