#!/usr/bin/env python3
"""
SSTR2 Peptide Binder Design Pipeline - Live Demo
=================================================
에이전트 파이프라인 전체 동작을 dry-run 모드로 실행하여 보여줍니다.

모든 외부 도구(RFdiffusion, ProteinMPNN, ESMFold, DiffDock, PyRosetta)는
mock 데이터로 대체되지만, 5개 에이전트(Planner, QCRanker, DiversityMgr,
Critic, Reporter)는 실제로 동작합니다.

Usage:
    python run_pipeline_demo.py
"""

from __future__ import annotations

import logging
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

from AG_src.schemas.io_schemas import (
    DockingResult, OffTargetDockingResult, QCResult, RosettaResult,
    SelectivityResult, SequenceEntry,
    Step01Output, Step02Output, Step03Output, Step04Output,
    Step05Output, Step05bOutput, Step06Output, Step07Output,
)

# ---------------------------------------------------------------------------
# Colorful logging setup
# ---------------------------------------------------------------------------

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[90m",      # gray
        "INFO": "\033[36m",       # cyan
        "WARNING": "\033[33m",    # yellow
        "ERROR": "\033[31m",      # red
        "CRITICAL": "\033[41m",   # red bg
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Agent-specific colors
    AGENT_COLORS = {
        "Planner": "\033[95m",         # magenta
        "QCRanker": "\033[92m",        # green
        "DiversityManager": "\033[96m", # bright cyan
        "ScientistCritic": "\033[93m",  # bright yellow
        "Reporter": "\033[94m",         # blue
    }

    def format(self, record):
        msg = super().format(record)
        level_color = self.COLORS.get(record.levelname, "")

        # Color agent names
        for agent, color in self.AGENT_COLORS.items():
            msg = msg.replace(f"[{agent}]", f"{color}{self.BOLD}[{agent}]{self.RESET}")

        # Color step names
        for step in ["step01", "step02", "step03", "step04", "step05", "step05b", "step06", "step07"]:
            msg = msg.replace(step, f"\033[32m{self.BOLD}{step}{self.RESET}")

        return f"{level_color}{msg}{self.RESET}"


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # Show agent logs too
    for name in ["co_scientist", "AG_src"]:
        lg = logging.getLogger(name)
        lg.setLevel(logging.INFO)
        lg.handlers = [handler]
        lg.propagate = False


# ---------------------------------------------------------------------------
# Mock data generators
# ---------------------------------------------------------------------------

def make_step01():
    return Step01Output(
        receptor_pdb_path="/tmp/sstr2_clean.pdb",
        pocket_residues=[122, 127, 184, 197, 205, 272, 294],
        chain_id="B",
        pocket_json_path="/tmp/pocket_residues.json",
    )

def make_step02():
    return Step02Output(
        backbone_pdbs=[f"/tmp/backbone_{i:02d}.pdb" for i in range(10)],
        design_params={"contigs": "B1-369/0 10-30", "hotspot_res": ["B122","B127","B184","B197","B205","B272","B294"]},
        n_generated=10,
    )

def make_step03():
    seqs = []
    for bb in range(10):
        for s in range(8):
            sid = f"bb{bb:02d}_seq{s:02d}"
            seqs.append(SequenceEntry(
                backbone_idx=bb, seq_idx=s,
                sequence="AGCKNFFWKTFTSC"[:10 + (bb + s) % 5],
                fasta_path=f"/tmp/{sid}.fasta", seq_id=sid,
            ))
    return Step03Output(sequences=seqs)

def make_step04():
    import random
    random.seed(42)
    results = []
    for bb in range(10):
        for s in range(8):
            sid = f"bb{bb:02d}_seq{s:02d}"
            plddt = random.gauss(78, 12)
            results.append(QCResult(
                seq_id=sid,
                plddt_mean=round(plddt, 1),
                plddt_interface=round(plddt - 3, 1),
                pdb_path=f"/tmp/{sid}_esm.pdb",
                passed_gate=plddt >= 75.0,
            ))
    return Step04Output(qc_results=results)

def make_step05(qc_passed):
    import random
    random.seed(42)
    results = []
    for i, qc in enumerate(qc_passed):
        score = random.gauss(-6.5, 2.0)
        results.append(DockingResult(
            seq_id=qc.seq_id, engine="diffdock",
            score=round(score, 2),
            confidence=round(random.uniform(0.6, 0.95), 2),
            pose_pdb=f"/tmp/{qc.seq_id}_pose.pdb", rank=1,
        ))
    results.sort(key=lambda x: x.score)
    return Step05Output(docking_results=results)

def make_step05b(docking_results):
    import random
    random.seed(42)
    sel_results, details = [], []
    for i, dr in enumerate(docking_results):
        ot_scores = {
            "SSTR1": round(dr.score + random.gauss(2.5, 0.8), 2),
            "SSTR3": round(dr.score + random.gauss(3.0, 1.0), 2),
            "SSTR4": round(dr.score + random.gauss(3.5, 0.5), 2),
            "SSTR5": round(dr.score + random.gauss(2.0, 0.7), 2),
        }
        worst = min(ot_scores.values())
        margin = round(worst - dr.score, 2)   # G-2: worst - sstr2 (양수=좋음)
        passed = margin >= 10.0 and worst >= -15.0
        sel_results.append(SelectivityResult(
            seq_id=dr.seq_id, sstr2_dock_score=dr.score,
            offtarget_scores=ot_scores, offtarget_max_score=worst,
            offtarget_max_receptor=min(ot_scores, key=ot_scores.get),
            selectivity_margin=margin, passed=passed,
        ))
        for name, sc in ot_scores.items():
            details.append(OffTargetDockingResult(
                seq_id=dr.seq_id, receptor_name=name,
                dock_score=sc, confidence=0.7, engine="diffdock",
            ))
    return Step05bOutput(selectivity_results=sel_results, offtarget_docking_details=details)

def make_step06(docking_results):
    import random
    random.seed(42)
    results = []
    for dr in docking_results:
        ddg = round(random.gauss(-6.0, 2.5), 1)
        results.append(RosettaResult(
            seq_id=dr.seq_id, ddg=ddg,
            total_score=round(-120 + random.gauss(0, 10), 1),
            clash_score=random.choice([0, 0, 0, 1]),
            constraint_violations=0,
            refined_pdb=f"/tmp/{dr.seq_id}_refined.pdb",
        ))
    return Step06Output(rosetta_results=results)

def make_step07():
    return Step07Output(
        lddt_table_path="/tmp/foldmason_lddt.json",
        pymol_renders={"overview": "/tmp/overview.png"},
        rank_table_csv="/tmp/rank_table.csv",
        summary_md="/tmp/summary.md",
    )


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def banner(text, char="=", width=72):
    print(f"\n\033[1;35m{char * width}")
    print(f"  {text}")
    print(f"{char * width}\033[0m\n")

def section(text, char="-", width=60):
    print(f"\n\033[1;33m{char * width}")
    print(f"  {text}")
    print(f"{char * width}\033[0m")

def show_candidates(label, candidates, limit=5):
    print(f"\n  \033[1m{label}\033[0m ({len(candidates)} total, showing top {min(limit, len(candidates))})")
    for c in candidates[:limit]:
        if hasattr(c, 'ddg'):
            print(f"    {c.seq_id:20s} | ddG={c.ddg:>6.1f} | clash={c.clash_score}")
        elif hasattr(c, 'score'):
            print(f"    {c.seq_id:20s} | dock={c.score:>7.2f} | conf={c.confidence:.2f}")
        elif hasattr(c, 'plddt_mean'):
            gate = "\033[32mPASS\033[0m" if c.passed_gate else "\033[31mFAIL\033[0m"
            print(f"    {c.seq_id:20s} | pLDDT={c.plddt_mean:>5.1f} | {gate}")

def show_selectivity(results, limit=5):
    print(f"\n  \033[1mSelectivity Results\033[0m ({len(results)} total)")
    for r in results[:limit]:
        gate = "\033[32mPASS\033[0m" if r.passed else "\033[31mFAIL\033[0m"
        print(f"    {r.seq_id:20s} | SSTR2={r.sstr2_dock_score:>7.2f} | margin={r.selectivity_margin:>6.2f} | {gate}")


# ---------------------------------------------------------------------------
# Main Demo
# ---------------------------------------------------------------------------

def run_demo():
    setup_logging()
    logger = logging.getLogger("demo")

    banner("SSTR2 Peptide Binder Design Pipeline - Live Demo")
    print("  Target:       SSTR2 (Somatostatin Receptor Type 2)")
    print("  Reference:    DOTATATE (AGCKNFFWKTFTSC)")
    print("  Off-targets:  SSTR1, SSTR3, SSTR4, SSTR5")
    print("  Iterations:   2 (dry-run mode)")
    print("  Agents:       Planner, QCRanker, DiversityMgr, Critic, Reporter")
    print("  LLM:          NoneProvider (rule-based mode)")
    print()

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Build orchestrator
        from AG_src.pipeline.orchestrator import PipelineOrchestrator

        orch = object.__new__(PipelineOrchestrator)
        orch._logger = logging.getLogger("orchestrator")
        orch.output_base = Path(tmp_dir) / "runs"
        orch.output_base.mkdir(parents=True, exist_ok=True)
        orch.gate_thresholds = {
            "esmfold_plddt_min": 75.0,
            "esmfold_interface_plddt_min": 70.0,
            "docking_top_pct": 20.0,
            "rosetta_ddg_max": -5.0,
            "rosetta_clash_max": 0,
            "selectivity_margin_min": 10.0,   # G-2: 양수=좋음
            "offtarget_max_allowed": -15.0,
            "final_score_weights": {},
        }
        orch.tool_registry = {}
        orch.config = {
            "run_id": "demo_run",
            "output_base_dir": str(orch.output_base),
            "iteration": {
                "max_iterations": 2,
                "n_backbone": 10,
                "k_seq_per_backbone": 8,
                "top_m_rosetta": 10,
                "diversity_top_n": 20,
            },
            "convergence_ddg_delta": 0.5,
            "convergence_patience": 3,
            "gate_thresholds": orch.gate_thresholds,
            "receptor": {"name": "SSTR2", "pdb_path": "/tmp/sstr2.pdb", "chain": "B"},
            "off_target_receptors": [
                {"name": "SSTR1"}, {"name": "SSTR3"},
                {"name": "SSTR4"}, {"name": "SSTR5"},
            ],
            "selectivity": {"enabled": True, "engine": "diffdock", "top_k_for_selectivity": 20},
            "reference_peptide": {"sequence": "AGCKNFFWKTFTSC"},
        }

        # Initialize agents
        orch._init_agents()

        # Show agent registry
        section("Agent Registry Initialized")
        for name, agent in orch._agents.items():
            print(f"  {agent}")

        # Prepare mock data
        step04_out = make_step04()
        qc_passed = step04_out.passed()
        step05_out = make_step05(qc_passed)
        step05b_out = make_step05b(step05_out.docking_results[:20])
        top_docking = step05_out.top_pct(pct=20.0)
        step06_out = make_step06(top_docking)

        # Patch external tools
        patches = {
            "AG_src.pipeline.step01_receptor.prepare_receptor": MagicMock(return_value=make_step01()),
            "AG_src.pipeline.step02_backbone.generate_backbones": MagicMock(return_value=make_step02()),
            "AG_src.pipeline.step03_sequence.design_sequences": MagicMock(return_value=make_step03()),
            "AG_src.pipeline.step04_qc.run_qc": MagicMock(return_value=step04_out),
            "AG_src.pipeline.step05_docking.run_docking": MagicMock(return_value=step05_out),
            "AG_src.pipeline.step05b_selectivity.run_selectivity_screening": MagicMock(return_value=step05b_out),
            "AG_src.pipeline.step06_rosetta.run_rosetta_refinement": MagicMock(return_value=step06_out),
            "AG_src.pipeline.step06_rosetta.apply_rosetta_gate": MagicMock(
                return_value=([r for r in step06_out.rosetta_results if r.ddg <= -5.0 and r.clash_score == 0],
                              [r for r in step06_out.rosetta_results if r.ddg > -5.0 or r.clash_score > 0])
            ),
            "AG_src.pipeline.step07_analysis.run_analysis": MagicMock(return_value=make_step07()),
        }

        def mock_setup_run(iteration):
            run_id = f"demo_{time.strftime('%Y%m%d_%H%M')}_iter{iteration:02d}"
            out_base = orch.output_base / run_id
            step_dirs = [
                "00_config", "01_receptor", "02_backbone", "03_sequence",
                "04_qc", "05_docking", "05b_selectivity", "06_rosetta",
                "07_viz", "08_reports",
            ]
            out_dirs = {}
            for sub in step_dirs:
                d = out_base / sub
                d.mkdir(parents=True, exist_ok=True)
                out_dirs[sub] = str(d)
            return run_id, out_dirs

        orch._setup_run = mock_setup_run

        # Track agent invocations
        agent_calls = []
        original_invoke = orch._invoke_agent

        def tracking_invoke(agent_name, context):
            t0 = time.time()
            section(f"Agent: {agent_name.upper()}")
            print(f"  Context keys: {list(context.keys())}")
            result = original_invoke(agent_name, context)
            elapsed = time.time() - t0
            agent_calls.append((agent_name, elapsed))

            # Show agent output
            content = result.content if hasattr(result, 'content') else result
            if isinstance(content, dict):
                for k, v in content.items():
                    if k == "status":
                        print(f"  Status: \033[32m{v}\033[0m")
                    elif k in ("plan", "experiment_plan"):
                        print(f"  Plan: {str(v)[:120]}...")
                    elif k == "rank_table":
                        print(f"  RankTable: {str(v)[:120]}...")
                    elif k == "critic_analysis":
                        print(f"  Analysis: {str(v)[:120]}...")
                    elif k == "diverse_candidates":
                        n = len(v) if isinstance(v, list) else "?"
                        print(f"  Diverse candidates: {n}")
                    elif k == "report_paths":
                        print(f"  Reports: {v}")
            print(f"  \033[90m({elapsed:.2f}s)\033[0m")
            return result

        orch._invoke_agent = tracking_invoke

        # === RUN PIPELINE ===
        banner("Starting Pipeline Execution (2 iterations)")

        with patch.multiple("AG_src.pipeline.step01_receptor",
                           prepare_receptor=patches["AG_src.pipeline.step01_receptor.prepare_receptor"]), \
             patch.multiple("AG_src.pipeline.step02_backbone",
                           generate_backbones=patches["AG_src.pipeline.step02_backbone.generate_backbones"]), \
             patch.multiple("AG_src.pipeline.step03_sequence",
                           design_sequences=patches["AG_src.pipeline.step03_sequence.design_sequences"]), \
             patch.multiple("AG_src.pipeline.step04_qc",
                           run_qc=patches["AG_src.pipeline.step04_qc.run_qc"]), \
             patch.multiple("AG_src.pipeline.step05_docking",
                           run_docking=patches["AG_src.pipeline.step05_docking.run_docking"]), \
             patch.multiple("AG_src.pipeline.step05b_selectivity",
                           run_selectivity_screening=patches["AG_src.pipeline.step05b_selectivity.run_selectivity_screening"]), \
             patch.multiple("AG_src.pipeline.step06_rosetta",
                           run_rosetta_refinement=patches["AG_src.pipeline.step06_rosetta.run_rosetta_refinement"],
                           apply_rosetta_gate=patches["AG_src.pipeline.step06_rosetta.apply_rosetta_gate"]), \
             patch.multiple("AG_src.pipeline.step07_analysis",
                           run_analysis=patches["AG_src.pipeline.step07_analysis.run_analysis"]):

            result = orch.run(max_iterations=2)

        # === RESULTS ===
        banner("Pipeline Execution Complete")

        print(f"  Total iterations:  {result.total_iterations}")
        print(f"  Converged:         {result.converged}")
        print(f"  Best candidates:   {len(result.best_candidates)}")
        if result.best_candidates:
            print(f"\n  \033[1mTop 5 Candidates:\033[0m")
            for i, c in enumerate(result.best_candidates[:5]):
                print(f"    #{i+1} {c.get('seq_id', c.get('candidate_id', '?')):20s} | "
                      f"ddG={c.get('ddg', 'N/A'):>6} | "
                      f"pLDDT={c.get('plddt', 'N/A')}")

        # Iteration details
        for ir in result.iteration_records:
            section(f"Iteration {ir.iteration} Summary")
            print(f"  Run ID:     {ir.run_id}")
            print(f"  Top ddG:    {ir.top_ddg}")
            print(f"  Passed QC:  {ir.n_passed_final}")
            print(f"  Hypothesis: {ir.hypothesis[:80]}..." if ir.hypothesis else "  Hypothesis: (rule-based)")
            steps_ok = sum(1 for s in ir.step_results.values() if s.success)
            steps_total = len(ir.step_results)
            color = "\033[32m" if steps_ok == steps_total else "\033[31m"
            print(f"  Steps:      {color}{steps_ok}/{steps_total} passed\033[0m")

        # Agent execution summary
        section("Agent Execution Summary")
        total_time = 0
        for name, elapsed in agent_calls:
            total_time += elapsed
            print(f"  {name:25s} | {elapsed:.3f}s")
        print(f"  {'TOTAL':25s} | {total_time:.3f}s")
        print(f"  Agent invocations: {len(agent_calls)}")

        # Show QC gate stats
        section("QC Gate Statistics")
        n_total = len(step04_out.qc_results)
        n_passed = len(qc_passed)
        n_failed = n_total - n_passed
        print(f"  Step04 ESMFold:     {n_passed}/{n_total} passed (pLDDT >= 75)")
        show_candidates("QC Passed (top 5)", qc_passed, 5)

        n_docked = len(step05_out.docking_results)
        n_top = len(top_docking)
        print(f"\n  Step05 Docking:     {n_top}/{n_docked} in top 20%")
        show_candidates("Docking Top 20%", top_docking, 5)

        n_sel = len(step05b_out.selectivity_results)
        n_sel_pass = len([r for r in step05b_out.selectivity_results if r.passed])
        print(f"\n  Step05b Selectivity: {n_sel_pass}/{n_sel} passed")
        show_selectivity(step05b_out.selectivity_results, 5)

        n_rosetta_pass = len([r for r in step06_out.rosetta_results if r.ddg <= -5.0 and r.clash_score == 0])
        print(f"\n  Step06 Rosetta:     {n_rosetta_pass}/{len(step06_out.rosetta_results)} passed (ddG <= -5.0)")
        show_candidates("Rosetta Results", step06_out.rosetta_results, 5)

        # Final report
        section("Final Report")
        if result.final_report_path:
            report = Path(result.final_report_path)
            if report.exists():
                content = report.read_text()
                lines = content.split("\n")
                print(f"  Path: {report}")
                print(f"  Lines: {len(lines)}")
                # Show first 20 lines
                for line in lines[:20]:
                    print(f"  | {line}")
                if len(lines) > 20:
                    print(f"  | ... ({len(lines) - 20} more lines)")

        banner("Demo Complete!", char="*")
        print("  All agents executed successfully in dry-run mode.")
        print("  To use real LLM: set llm.provider='ollama' in pipeline_config.yaml")
        print("  To use real APIs: set NVIDIA_NIM_API_KEY environment variable")
        print()


if __name__ == "__main__":
    run_demo()
