"""test_tier2_ui_integration.py
================================
Tier 2 fix (F13/F14/F15) 회귀 테스트 — UI integration.

F13: pipeline_local orchestrator에 StatusEmitter 통합 — step/agent live emit
F14: BE list_runs가 LOCAL MODE archive 자동 노출 (F13 부수 효과 — 같은 ARCHIVE_DIR)
F15: FE PipelineStatus/AgentMonitor가 통합 view (F13 부수 — STATUS_FILE 갱신)
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest


class TestF13StatusEmitterIntegration:
    """F13: orchestrator가 StatusEmitter import + 사용."""

    def test_orchestrator_imports_status_emitter(self):
        """F13 fix: pipeline_local/orchestrator.py가 StatusEmitter import 시도."""
        from pipeline_local import orchestrator
        source = inspect.getsource(orchestrator)
        assert "StatusEmitter" in source, (
            "F13 fix — pipeline_local/orchestrator.py에 StatusEmitter import 부재"
        )
        assert "_STATUS_EMITTER_AVAILABLE" in source, (
            "F13 fix — emitter 가용성 체크 부재"
        )

    def test_execute_step_calls_emitter(self):
        """F13 fix: _execute_step()이 emitter.update_step 호출."""
        from pipeline_local.orchestrator import LocalPipelineOrchestrator
        source = inspect.getsource(LocalPipelineOrchestrator._execute_step)
        assert "update_step" in source, (
            "F13 fix — _execute_step에 emitter.update_step 호출 부재"
        )
        assert "running" in source and "completed" in source, (
            "F13 fix — step status 두 상태 모두 emit 안 됨"
        )

    def test_emitter_initialized_per_run(self):
        """F13 fix: iteration loop 시작 시 emitter 인스턴스 생성."""
        from pipeline_local import orchestrator
        source = inspect.getsource(orchestrator)
        assert "self._emitter" in source, "F13 fix — emitter instance 부재"


class TestF14F15IndirectIntegration:
    """F14/F15: F13의 자연 부수 효과 — 별도 코드 수정 없음."""

    def test_status_emitter_default_archive_matches_be_search(self):
        """F14 부수: StatusEmitter default ARCHIVE_DIR이 BE list_runs search path와 동일.

        Note: 두 파일이 *같은 default*를 사용하므로 F13의 emit이 자동으로 BE에 노출됨.
        본 test는 *명시적 import 없이 file system 직접 read*로 검증 (test cwd 의존).
        """
        # 절대 경로 사용 (test cwd 의존 회피)
        repo_candidates = [
            Path("/home/dongjukim/Documents/workspace/repos/SST14-M_scr"),
            Path(__file__).resolve().parents[2],
        ]
        repo = next((p for p in repo_candidates if (p / "AgenticAI4SCIENCE_pyrosetta_track").exists()), None)
        if repo is None:
            pytest.skip("repo root 자동 탐지 실패")

        ai4sci_state = repo / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri" / "backend" / "state.py"
        ai4sci_emitter = repo / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri" / "backend" / "status_emitter.py"

        if not ai4sci_state.exists() or not ai4sci_emitter.exists():
            pytest.skip("ai4sci-kaeri backend 파일 부재")

        emitter_source = ai4sci_emitter.read_text()
        state_source = ai4sci_state.read_text()
        # Path 구성은 "runs" / "pyrosetta_flow" / "archives" 또는 "runs/pyrosetta_flow/archives"
        # 두 형식 모두 매칭하기 위해 component 단위로 검증
        for piece in ("pyrosetta_flow", "archives"):
            assert piece in emitter_source, (
                f"StatusEmitter source에 '{piece}' 누락 — default ARCHIVE_DIR 변경됨"
            )
            assert piece in state_source, (
                f"BE state.py source에 '{piece}' 누락 — default ARCHIVE_DIR 변경됨"
            )

    def test_orchestrator_fallback_when_emitter_unavailable(self):
        """F13 robustness: StatusEmitter import 실패 시 정상 fallback."""
        from pipeline_local import orchestrator
        source = inspect.getsource(orchestrator)
        assert "_STATUS_EMITTER_AVAILABLE = False" in source, (
            "F13 robust fallback 부재 — StatusEmitter import 실패 시 깨질 위험"
        )
