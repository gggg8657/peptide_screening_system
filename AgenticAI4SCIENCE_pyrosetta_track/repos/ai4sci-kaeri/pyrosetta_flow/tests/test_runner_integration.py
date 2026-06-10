"""Integration tests for run_pyrosetta_agentic_mutdock_flow().

All external dependencies (subprocess, agents, StatusEmitter, file I/O)
are mocked to verify orchestration logic end-to-end.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pyrosetta_flow.schema import FlowArtifacts, FlowConfig


@pytest.fixture()
def integration_config(tmp_path) -> FlowConfig:
    """Config for integration tests with real tmp_path paths."""
    pdb = tmp_path / "template.pdb"
    pdb.write_text("ATOM 1 N ALA A 1 0 0 0 1 0\nEND\n")
    return FlowConfig(
        template_pdb=str(pdb),
        original_sequence="AGCKNFFWKTFTSC",
        design_positions=[1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14],
        n_candidates=2,
        seed_base=42,
        output_dir=str(tmp_path / "runs"),
        max_iterations=1,
        top_k=2,
    )


@pytest.fixture()
def _mock_all_externals(integration_config):
    """Mock every external dependency of runner.py for integration testing."""
    patches = []

    def _start(target):
        p = patch(target)
        m = p.start()
        patches.append(p)
        return m

    # --- subprocess / script execution ---
    mock_run_script = _start("pyrosetta_flow.runner._run_script")
    mock_run_script.return_value = {
        "ddg": -8.5,
        "total_score": -120.0,
        "clash_score": 2.0,
    }

    # --- LLM provider ---
    mock_create = _start("pyrosetta_flow.runner.create_provider")
    mock_create.return_value = MagicMock(__str__=lambda self: "mock-llm")

    # --- StatusEmitter ---
    mock_emitter_cls = _start("pyrosetta_flow.runner.StatusEmitter")
    emitter_inst = MagicMock()
    emitter_inst.start_step.return_value = 0.0
    emitter_inst.start_rosetta_substep.return_value = 0.0
    mock_emitter_cls.return_value = emitter_inst

    # --- PlannerAgent ---
    mock_planner_cls = _start("pyrosetta_flow.runner.PlannerAgent")
    plan_mock = MagicMock()
    plan_mock.hypothesis = "Integration test hypothesis"
    plan_mock.parameters = {"mutation_guidance": {"focus_positions": [5, 6]}}
    mock_planner_cls.return_value.execute.return_value = {"plan": plan_mock}

    # --- CriticAgent ---
    mock_critic_cls = _start("pyrosetta_flow.runner.ScientistCriticAgent")
    critic_mock = MagicMock()
    critic_mock.hypothesis = "Critic integration feedback"
    critic_mock.proposed_changes = []
    mock_critic_cls.return_value.execute.return_value = {"critic_analysis": critic_mock}

    # --- QCRankerAgent ---
    mock_qcranker_cls = _start("pyrosetta_flow.runner.QCRankerAgent")

    def qc_execute(payload):
        # Return top candidates from input
        candidates = payload.get("candidates", [])
        top = candidates[:payload.get("top_k", 2)]
        return {
            "top_candidates": top,
            "rank_table": [{"id": c.candidate_id, "ddg": c.ddg} for c in top],
            "qc_report": {"total": len(candidates), "passed": len(top)},
        }
    mock_qcranker_cls.return_value.execute.side_effect = qc_execute

    # --- ReporterAgent ---
    mock_reporter_cls = _start("pyrosetta_flow.runner.ReporterAgent")
    mock_reporter_cls.return_value.execute.return_value = {
        "report_paths": {"summary_md": "/tmp/summary.md", "rank_csv": "/tmp/rank.csv"},
    }

    # --- Pipeline config ---
    _start("pyrosetta_flow.runner._read_pipeline_config").return_value = {}

    yield {
        "run_script": mock_run_script,
        "emitter": emitter_inst,
        "planner": mock_planner_cls,
        "critic": mock_critic_cls,
        "qcranker": mock_qcranker_cls,
        "reporter": mock_reporter_cls,
    }

    for p in patches:
        p.stop()


class TestRunFlowIntegration:

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_baseline_success(self, integration_config, _mock_all_externals):
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        assert isinstance(result, FlowArtifacts)
        assert result.run_id.startswith("sst14_mutdock_")
        # _run_script should have been called (baseline + candidates)
        assert _mock_all_externals["run_script"].call_count >= 1

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_one_iteration_produces_candidates(self, integration_config, _mock_all_externals):
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        assert len(result.iterations) == 1
        iter_data = result.iterations[0]
        assert "candidates" in iter_data
        assert len(iter_data["candidates"]) == integration_config.n_candidates

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_candidate_sequences_are_mutated(self, integration_config, _mock_all_externals):
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        for cand in result.iterations[0]["candidates"]:
            # No candidate should be the native sequence
            assert cand["sequence"] != integration_config.original_sequence

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_candidate_sequences_preserve_fwkt_pharmacophore(self, integration_config, _mock_all_externals):
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        for cand in result.iterations[0]["candidates"]:
            assert cand["sequence"][6:10] == integration_config.original_sequence[6:10]

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_candidates_fail_when_only_fwkt_positions_are_designable(self, integration_config, _mock_all_externals):
        integration_config.design_positions = [7, 8, 9, 10]
        integration_config.validation_n_trials = 1  # validation 비활성화 (FWKT gate 테스트 목적)

        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        candidates = result.iterations[0]["candidates"]
        assert len(candidates) == integration_config.n_candidates
        assert all(c["fail_reason"] == "FWKT pharmacophore gate failed after 3 retries" for c in candidates)
        assert _mock_all_externals["run_script"].call_count == 1

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_agents_called(self, integration_config, _mock_all_externals):
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        run_pyrosetta_agentic_mutdock_flow(integration_config)
        # Each agent should be called at least once
        assert _mock_all_externals["planner"].return_value.execute.call_count >= 1
        assert _mock_all_externals["critic"].return_value.execute.call_count >= 1
        assert _mock_all_externals["qcranker"].return_value.execute.call_count >= 1
        assert _mock_all_externals["reporter"].return_value.execute.call_count >= 1

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_emitter_lifecycle(self, integration_config, _mock_all_externals):
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        run_pyrosetta_agentic_mutdock_flow(integration_config)
        emitter = _mock_all_externals["emitter"]
        emitter.set_completed.assert_called_once()
        assert emitter.set_candidates.call_count >= 1

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_summary_fields(self, integration_config, _mock_all_externals):
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        assert result.summary["mode"] == "agentic_mutate_then_dock"
        assert "run_status" in result.summary
        assert "best_final_ddg" in result.summary

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_multi_iteration(self, integration_config, _mock_all_externals):
        """Test with 2 iterations."""
        integration_config.max_iterations = 2
        _mock_all_externals["emitter"].start_step.return_value = 0.0
        _mock_all_externals["emitter"].start_rosetta_substep.return_value = 0.0

        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        assert len(result.iterations) == 2

    @pytest.mark.usefixtures("_mock_all_externals")
    def test_baseline_failure_continues(self, integration_config, _mock_all_externals):
        """When baseline fails, flow continues (fail-open)."""
        call_count = [0]
        original_return = _mock_all_externals["run_script"].return_value

        def fail_baseline_then_succeed(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 3:  # 3 baseline trials
                raise RuntimeError("Baseline failed")
            return original_return

        _mock_all_externals["run_script"].side_effect = fail_baseline_then_succeed

        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        result = run_pyrosetta_agentic_mutdock_flow(integration_config)
        assert isinstance(result, FlowArtifacts)
        # Should still have iterations despite baseline failure
        assert len(result.iterations) >= 1
