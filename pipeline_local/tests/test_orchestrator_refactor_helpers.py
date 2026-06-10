from __future__ import annotations

import logging
from types import SimpleNamespace

from pipeline_local.orchestrator import (
    BranchOutputs,
    LocalPipelineOrchestrator,
    SequenceEntry,
)
from pipeline_local.schemas.io_schemas import DockingResult


def test_compute_gate_stats_calculates_failed_count():
    stats = LocalPipelineOrchestrator._compute_gate_stats(
        total=7,
        passed=3,
        threshold="top 20%",
    )

    assert stats.passed == 3
    assert stats.failed == 4
    assert stats.threshold == "top 20%"


def test_run_dual_silo_prefixes_silo_a_seq_ids():
    orch = LocalPipelineOrchestrator.__new__(LocalPipelineOrchestrator)

    silo_a = [
        SequenceEntry(backbone_idx=0, seq_idx=0, sequence="AAAA", fasta_path="", seq_id="cand_1"),
        SequenceEntry(backbone_idx=0, seq_idx=1, sequence="BBBB", fasta_path="", seq_id="cand_2"),
    ]
    silo_b = [SimpleNamespace(seq_id="b_seed_1")]

    result = orch._run_dual_silo(silo_a, silo_b)

    assert isinstance(result, BranchOutputs)
    assert [seq.seq_id for seq in result.step03_out.sequences] == ["a_cand_1", "a_cand_2"]
    assert result.silo_b_rosetta_results == silo_b
    assert result.dual_mode is True


def test_run_diversity_filter_respects_agent_selected_ids():
    orch = LocalPipelineOrchestrator.__new__(LocalPipelineOrchestrator)
    orch._logger = logging.getLogger("test.orchestrator.refactor")
    orch._invoke_agent = lambda *_args, **_kwargs: SimpleNamespace(
        content={"selected_seq_ids": ["cand_b"]}
    )

    top_docking = [
        DockingResult(
            seq_id="cand_a",
            engine="boltz2",
            score=-10.0,
            confidence=0.9,
            pose_pdb="a.pdb",
            rank=1,
        ),
        DockingResult(
            seq_id="cand_b",
            engine="boltz2",
            score=-9.0,
            confidence=0.8,
            pose_pdb="b.pdb",
            rank=2,
        ),
    ]

    filtered = orch._run_diversity_filter(top_docking)

    assert [cand.seq_id for cand in filtered] == ["cand_b"]
