from __future__ import annotations

import logging
import sys
import types
from types import SimpleNamespace


def test_silo_b_uses_reference_peptide_sequence_from_config(monkeypatch, tmp_path):
    from pipeline_local.orchestrator import (
        DEFAULT_REFERENCE_PEPTIDE_SEQUENCE,
        LocalPipelineOrchestrator,
    )

    captured: dict[str, str] = {}

    class FakeFlowConfig:
        def __init__(self, **kwargs):
            captured["original_sequence"] = kwargs["original_sequence"]
            self.seed_base = kwargs["seed_base"]

    def fake_run_pyrosetta_agentic_mutdock_flow(_flow_config):
        return SimpleNamespace(final_candidates=[], iterations=[])

    monkeypatch.setitem(
        sys.modules,
        "pyrosetta_flow.runner",
        types.SimpleNamespace(
            run_pyrosetta_agentic_mutdock_flow=fake_run_pyrosetta_agentic_mutdock_flow
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "pyrosetta_flow.schema",
        types.SimpleNamespace(FlowConfig=FakeFlowConfig),
    )

    orch = LocalPipelineOrchestrator.__new__(LocalPipelineOrchestrator)
    orch._logger = logging.getLogger("test.orchestrator")
    orch.config = {
        "dual_silo": {"silo_b": {}},
        "receptor": {"existing_pdb": str(tmp_path / "receptor.pdb")},
        "iteration": {"n_candidates": 8},
        "llm": {},
        "run_id": "test_run",
    }
    orch.gate_thresholds = {}
    orch.output_base = tmp_path
    orch._reference_peptide_sequence = "OVERRIDESEQ"

    step01_out = SimpleNamespace(receptor_pdb_path=str(tmp_path / "fallback_receptor.pdb"))

    result = orch._run_silo_b(step01_out=step01_out, iteration=1)

    assert result == []
    assert captured["original_sequence"] == "OVERRIDESEQ"
    assert captured["original_sequence"] != DEFAULT_REFERENCE_PEPTIDE_SEQUENCE
