#!/usr/bin/env python3
"""
SSTR2 Peptide Binder Pipeline - Live NIM API Demo
==================================================
?ㅼ젣 NVIDIA NIM API (ESMFold, MolMIM)瑜??몄텧?섎㈃???먯씠?꾪듃 ?뚯씠?꾨씪???꾩껜瑜??ㅽ뻾?⑸땲??

Available APIs:
  - ESMFold (200 OK) ??援ъ“ ?덉륫 + pLDDT QC
  - MolMIM  (200 OK) ??遺꾩옄 ?앹꽦/理쒖쟻??  - DiffDock, RFdiffusion, ProteinMPNN ??dry-run (mock)

Usage:
    export NVIDIA_NIM_API_KEY="nvapi-..."
    python run_pipeline_live.py
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from backend.status_emitter import StatusEmitter

# Global emitter instance
emitter: Optional[StatusEmitter] = None

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[90m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RED = "\033[31m"
WHITE = "\033[97m"
BG_GREEN = "\033[42m"
BG_BLUE = "\033[44m"

def p(msg, color=CYAN): print(f"{DIM}{time.strftime('%H:%M:%S')}{RESET} {color}{msg}{RESET}")
def banner(text, char="=", width=72): print(f"\n{BOLD}{MAGENTA}{char*width}\n  {text}\n{char*width}{RESET}\n")
def step_h(name, desc): print(f"\n  {BG_BLUE}{WHITE}{BOLD} {name} {RESET}  {desc}\n  {'-'*60}")
def agent_h(name):
    c = {"Planner":MAGENTA,"QCRanker":GREEN,"DiversityManager":CYAN,"ScientistCritic":YELLOW,"Reporter":BLUE}.get(name,WHITE)
    print(f"\n  {c}{BOLD}Agent: {name}{RESET}")
def ok(msg): print(f"    {GREEN}[OK]{RESET} {msg}")
def fail(msg): print(f"    {RED}[FAIL]{RESET} {msg}")
def info(msg): print(f"    {DIM}[INFO]{RESET} {msg}")

logging.basicConfig(level=logging.WARNING)


def _run_pyrosetta_flow_if_requested() -> bool:
    """`--enable-pyrosetta-flow`媛 ?덉쑝硫??명듃遺??곹빀 寃쎈줈留??ㅽ뻾?쒕떎."""
    if "--enable-pyrosetta-flow" not in sys.argv:
        return False

    def _value_after(flag: str, default: str) -> str:
        if flag not in sys.argv:
            return default
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
        return default

    pyro_input = _value_after("--pyrosetta-input", "")
    if not pyro_input:
        print(f"{RED}ERROR:{RESET} --enable-pyrosetta-flow requires --pyrosetta-input <template_pdb>")
        sys.exit(2)

    pyro_output = _value_after(
        "--pyrosetta-output",
        "runs/pyrosetta_flow/pyrosetta_flow_artifacts.json",
    )
    conda_env = _value_after("--pyrosetta-conda-env", "bio-tools")
    n_candidates = int(_value_after("--pyrosetta-n-candidates", "3"))

    from pyrosetta_flow import FlowConfig, run_pyrosetta_notebook_flow

    cfg = FlowConfig(
        template_pdb=pyro_input,
        n_candidates=n_candidates,
        conda_env=conda_env,
    )
    artifacts = run_pyrosetta_notebook_flow(cfg)
    artifacts.write_json(pyro_output)
    print(f"{GREEN}[pyrosetta_flow]{RESET} artifacts saved -> {pyro_output}")
    return True

# ---------------------------------------------------------------------------
# Direct NIM API callers (correct payload format)
# ---------------------------------------------------------------------------
API_KEY = None
BASE = "https://health.api.nvidia.com/v1"

def nim_post(endpoint: str, payload: dict, timeout: int = 120) -> Optional[dict]:
    url = f"{BASE}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        fail(f"HTTP {e.code}: {body}")
        return None
    except Exception as e:
        fail(f"Error: {e}")
        return None


def esmfold_predict(sequence: str, retries: int = 2) -> Optional[dict]:
    """ESMFold: sequence ??PDB structure (with retry)."""
    for attempt in range(retries + 1):
        result = nim_post("/biology/nvidia/esmfold", {"sequence": sequence})
        if result is not None:
            return result
        if attempt < retries:
            wait = 2 * (attempt + 1)
            info(f"  ?ъ떆??{attempt+2}/{retries+1} ({wait}s ?湲?..)")
            time.sleep(wait)
    return None


def molmim_generate(smiles: str, n: int = 3) -> Optional[dict]:
    """MolMIM: SMILES ??optimized molecules."""
    return nim_post("/biology/nvidia/molmim/generate", {
        "smi": smiles, "num_molecules": n, "algorithm": "CMA-ES",
    })


def extract_plddt_from_pdb(pdb_text: str) -> List[float]:
    """PDB ATOM records??B-factor 而щ읆?먯꽌 pLDDT 媛믪쓣 異붿텧?쒕떎."""
    plddts = []
    for line in pdb_text.splitlines():
        if line.startswith("ATOM") and len(line) >= 66:
            try:
                bfactor = float(line[60:66].strip())
                plddts.append(bfactor)
            except ValueError:
                pass
    return plddts


def _parse_main_args() -> argparse.Namespace:
    """Parse CLI args for full pipeline mode."""
    parser = argparse.ArgumentParser(
        description="Run SSTR2 live pipeline with configurable iteration/model settings.",
    )
    parser.add_argument("--max-iterations", type=int, default=None)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--llm-provider", choices=["none", "ollama", "vllm"], default=None)
    parser.add_argument("--llm-model", type=str, default=None)
    parser.add_argument("--llm-base-url", type=str, default=None)
    parser.add_argument("--llm-timeout", type=int, default=None)
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = _parse_main_args()
    global API_KEY
    API_KEY = os.environ.get("NVIDIA_NIM_API_KEY")
    if not API_KEY:
        print(f"  {RED}ERROR: NVIDIA_NIM_API_KEY not set{RESET}")
        sys.exit(1)

    banner("SSTR2 Peptide Binder Design - Live NIM API Pipeline")
    print(f"  {GREEN}API Key:{RESET}  {API_KEY[:12]}...{API_KEY[-4:]}")
    print(f"  {GREEN}Target:{RESET}   SSTR2 (Somatostatin Receptor Type 2)")
    print(f"  {GREEN}Ref:{RESET}      DOTATATE (AGCKNFFWKTFTSC, 14-aa)")
    print(f"  {GREEN}APIs:{RESET}     ESMFold (live), MolMIM (live), others (dry-run)")
    print()

    # Load pipeline config for Approach B settings
    config_path = Path(__file__).parent / "AG_src" / "config" / "pipeline_config.yaml"
    pipeline_cfg: Dict[str, Any] = {}
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            pipeline_cfg = yaml.safe_load(f) or {}

    # Runtime overrides via CLI
    llm_cfg = pipeline_cfg.setdefault("llm", {})
    if args.llm_provider:
        llm_cfg["provider"] = args.llm_provider
    if args.llm_model:
        llm_cfg["model"] = args.llm_model
    if args.llm_base_url:
        llm_cfg["base_url"] = args.llm_base_url
    if args.llm_timeout is not None:
        llm_cfg["timeout"] = int(args.llm_timeout)

    iter_cfg = pipeline_cfg.setdefault("iteration", {})
    if args.max_iterations is not None:
        iter_cfg["max_iterations"] = max(1, int(args.max_iterations))

    approach_b_cfg = pipeline_cfg.get("approach_b", {})
    approach_b_enabled = approach_b_cfg.get("enabled", False)
    if approach_b_enabled:
        print(f"  {BOLD}{MAGENTA}Approach B (BLOSUM62 Text-Level Mutation) ENABLED{RESET}")
    else:
        print(f"  {DIM}Approach A (RFdiffusion ??ProteinMPNN) mode{RESET}")
    print()

    # Resolve iteration/run metadata before emitter initialization
    iter_cfg = pipeline_cfg.get("iteration", {})
    max_iterations = int(iter_cfg.get("max_iterations", 5))
    run_id = args.run_id or f"live_run_{time.strftime('%Y%m%d_%H%M%S')}"

    # Initialize monitoring emitter
    global emitter
    emitter = StatusEmitter(run_id=run_id, total_iterations=max_iterations)
    p(f"Dashboard emitter initialized ??/tmp/ag_pipeline_status.json (run_id={run_id})")

    # ===================================================================
    # STEP 1: Health Check
    # ===================================================================
    step_h("PHASE 1", "NIM API ?ъ뒪泥댄겕")
    t_health = emitter.start_step("step01")
    endpoints = {
        "ESMFold": "/biology/nvidia/esmfold",
        "MolMIM": "/biology/nvidia/molmim/generate",
    }
    for name, ep in endpoints.items():
        t0 = time.time()
        result = nim_post(ep, {"sequence": "MKTL"} if "esmfold" in ep else {"smi": "C", "num_molecules": 1, "algorithm": "CMA-ES"}, timeout=15)
        elapsed = time.time() - t0
        api_key_name = "esmfold" if "esmfold" in ep else "molmim"
        if result:
            ok(f"{name:15s} ??{GREEN}LIVE{RESET} ({elapsed:.2f}s)")
            emitter.set_api_status(api_key_name, "live")
        else:
            fail(f"{name:15s} ???곌껐 ?ㅽ뙣")
            emitter.set_api_status(api_key_name, "failed")
    emitter.complete_step("step01", t_health)

    # ===================================================================
    # ITERATION CONFIG
    # ===================================================================
    iter_cfg = pipeline_cfg.get("iteration", {})
    adaptive = iter_cfg.get("adaptive_enabled", True)
    conv_min_cands = int(iter_cfg.get("convergence_min_candidates", 3))
    conv_ddg_thresh = float(iter_cfg.get("convergence_ddg_threshold", -30.0))
    patience = int(iter_cfg.get("no_improvement_patience", 2))
    min_iterations = int(iter_cfg.get("min_iterations", 2))

    # Track convergence across iterations
    all_candidates_history: List[Dict[str, Any]] = []
    convergence_log: List[Dict[str, Any]] = []
    no_improvement_count = 0
    prev_best_ddg = 0.0

    # Read gate config once (used inside the loop)
    gate_cfg = pipeline_cfg.get("gate_thresholds", {})
    if not gate_cfg:
        gate_path = Path(__file__).parent / "AG_src" / "config" / "gate_thresholds.yaml"
        if gate_path.exists():
            with open(gate_path, encoding="utf-8") as gf:
                gate_cfg = yaml.safe_load(gf) or {}
    plddt_threshold = float(gate_cfg.get("esmfold_plddt_min", 75.0))

    # Read Rosetta config once (used inside the loop)
    from AG_src.pipeline.step06_rosetta import is_pyrosetta_available
    from AG_src.schemas.rank_table import compute_final_score

    rosetta_cfg = pipeline_cfg.get("rosetta", {})
    rosetta_enabled = rosetta_cfg.get("enabled", True)
    rosetta_fallback = rosetta_cfg.get("fallback_to_simulation", True)
    rosetta_top_m = rosetta_cfg.get("top_m_rosetta", 5)
    rosetta_ddg_max = float(gate_cfg.get("rosetta_ddg_max", -5.0))
    rosetta_clash_max = int(gate_cfg.get("rosetta_clash_max", 5))

    # Import agents once (used inside the loop)
    from AG_src.llm import create_provider
    from AG_src.agents.planner import PlannerAgent
    from AG_src.agents.qc_ranker import QCRankerAgent, Candidate
    from AG_src.agents.diversity_manager import DiversityManagerAgent
    from AG_src.agents.critic import ScientistCriticAgent
    from AG_src.agents.reporter import ReporterAgent
    from AG_src.pipeline.step05b_selectivity import compute_selectivity_margin, SelectivityResult

    llm = create_provider(pipeline_cfg)
    emitter.set_llm_model(str(llm))

    # Variables that persist across iterations for final summary
    DOTATATE = "AGCKNFFWKTFTSC"
    critic_result: Optional[Dict[str, Any]] = None
    final_qc_results: List[Dict[str, Any]] = []
    final_dock_results: List[Dict[str, Any]] = []
    final_rosetta_results: List[Dict[str, Any]] = []
    final_sel_results: List[Any] = []
    final_n_passed = 0
    final_n_failed = 0
    final_n_ros_pass = 0
    final_n_sel_pass = 0
    final_n_to_fold = 0
    rosetta_mode_label = "simulated"

    # Approach B variables that persist for summary
    step03b_output = None
    n_singles = 0
    n_combos = 0
    passed_prescreen: List[Dict[str, Any]] = []
    failed_prescreen: List[Dict[str, Any]] = []
    prescreen_min_hours = 0.0
    backbones: List[Dict[str, Any]] = []
    all_sequences: List[Dict[str, Any]] = []

    for current_iteration in range(1, max_iterations + 1):
        # Update dashboard iteration counter and reset steps
        emitter.set_iteration(current_iteration)
        if current_iteration > 1:
            emitter.reset_steps(skip_steps=["step01"])
        iter_header = f"ITERATION {current_iteration}/{max_iterations}"
        print(f"\n  {'='*60}")
        print(f"  {BOLD}{MAGENTA} {iter_header} {RESET}")
        print(f"  {'='*60}\n")

        # Reset per-iteration results
        qc_results: List[Dict[str, Any]] = []
        dock_results: List[Dict[str, Any]] = []
        sel_results: List[Any] = []
        rosetta_results: List[Dict[str, Any]] = []

        # ===============================================================
        # APPROACH A/B BRANCHING
        # ===============================================================

        if approach_b_enabled:
            # ===========================================================
            # APPROACH B: BLOSUM62 Text-Level Mutation
            # ===========================================================

            # Skip Step 02 (RFdiffusion) and Step 03 (ProteinMPNN)
            emitter.update_step("step02", "skipped")
            emitter.update_step("step03", "skipped")

            # --- STEP 03b: BLOSUM62 Mutation ---
            step_h("STEP 03b", f"BLOSUM62 - ?띿뒪???덈꺼 ?쒗??蹂???앹꽦 ({BOLD}{MAGENTA}Approach B{RESET})")
            t_step03b = emitter.start_step("step03b")

            from AG_src.pipeline.step03b_blosum_mutation import (
                run_approach_b, validate_constraints,
            )

            step03b_output = run_approach_b(pipeline_cfg)
            n_singles = sum(1 for v in step03b_output.variants if v.source == "single_mutant")
            n_combos = sum(1 for v in step03b_output.variants if v.source == "combinatorial")
            ok(f"{step03b_output.total_generated}媛?蹂?댁껜 ?앹꽦 (?⑥씪: {n_singles}, 議고빀: {n_combos})")
            for v in step03b_output.variants[:5]:
                info(f"{v.variant_id}: {v.sequence}  mutations={v.mutations}  BLOSUM={v.blosum_total_score}")
            if step03b_output.total_generated > 5:
                info(f"... +{step03b_output.total_generated - 5} more variants")

            # Fixed positions verification
            fixed_pos = step03b_output.fixed_positions
            ok(f"怨좎젙 ?꾩튂: {fixed_pos}")
            n_valid = sum(1 for v in step03b_output.variants if validate_constraints(v.sequence, fixed_pos))
            ok(f"?쒖빟 議곌굔 寃利? {n_valid}/{step03b_output.total_generated} ?듦낵")
            emitter.complete_step("step03b", t_step03b)

            # --- STEP 03b-QC: Stability Pre-screening ---
            step_h("STEP 03b-QC", f"?덉젙???ъ쟾 ?ㅽ겕由щ떇 ({BOLD}{YELLOW}Stability-First{RESET})")
            t_step03b_qc = emitter.start_step("step03b_qc")

            from AG_src.pipeline.step08_stability import predict_half_life

            prescreen_min_hours = float(approach_b_cfg.get("stability_prescreen_min_hours", 50.0))
            prescreen_results = []
            for v in step03b_output.variants:
                hl = predict_half_life(v.sequence, [])
                prescreen_results.append({
                    "variant": v,
                    "half_life_hours": round(hl, 2),
                    "passed": hl >= prescreen_min_hours,
                })

            passed_prescreen = [r for r in prescreen_results if r["passed"]]
            failed_prescreen = [r for r in prescreen_results if not r["passed"]]

            n_pass = len(passed_prescreen)
            n_fail = len(failed_prescreen)
            print(f"\n    {BOLD}Stability Pre-screen: {GREEN}{n_pass} passed{RESET} / {RED}{n_fail} failed{RESET} "
                  f"(half-life >= {prescreen_min_hours}h)")

            for r in sorted(passed_prescreen, key=lambda x: -x["half_life_hours"])[:5]:
                v = r["variant"]
                info(f"{v.variant_id}: {v.sequence}  t쩍={r['half_life_hours']:.1f}h  {GREEN}PASS{RESET}")
            for r in sorted(failed_prescreen, key=lambda x: x["half_life_hours"])[:3]:
                v = r["variant"]
                info(f"{v.variant_id}: {v.sequence}  t쩍={r['half_life_hours']:.1f}h  {RED}FAIL{RESET}")

            emitter.complete_step("step03b_qc", t_step03b_qc)

            # Convert passed variants to all_sequences format for downstream steps
            all_sequences = []
            for i, r in enumerate(sorted(passed_prescreen, key=lambda x: -x["half_life_hours"])):
                v = r["variant"]
                all_sequences.append({
                    "seq_id": v.variant_id,
                    "backbone_id": "blosum_b",
                    "sequence": v.sequence,
                    "half_life_hours": r["half_life_hours"],
                    "mutations": v.mutations,
                    "blosum_score": v.blosum_total_score,
                })

            ok(f"{len(all_sequences)}媛?蹂?댁껜 ??ESMFold QC濡??꾨떖")

        else:
            # ===========================================================
            # APPROACH A: RFdiffusion ??ProteinMPNN (湲곗〈 濡쒖쭅)
            # ===========================================================

            # --- STEP 2: Backbone generation ---
            step_h("STEP 02", "RFdiffusion - 諛깅낯 ?앹꽦 (dry-run mock)")
            t_step02 = emitter.start_step("step02")

            n_backbone = 5
            backbones = []
            for i in range(n_backbone):
                random.seed(42 + i)
                length = random.randint(10, 25)
                backbones.append({"id": f"backbone_{i:02d}", "length": length, "pdb": f"MOCK-BB-{i}"})
                info(f"backbone_{i:02d}: {length}-residue peptide (mock)")
            ok(f"{n_backbone}媛?諛깅낯 ?앹꽦 (dry-run)")
            emitter.complete_step("step02", t_step02)

            # --- STEP 3: Sequence design ---
            step_h("STEP 03", "ProteinMPNN - ?쒗???ㅺ퀎 (dry-run mock)")
            t_step03 = emitter.start_step("step03")

            amino_acids = "ACDEFGHIKLMNPQRSTVWY"
            all_sequences = []
            for bb in backbones:
                for j in range(4):
                    random.seed(hash(f"{bb['id']}_{j}") % 2**32)
                    length = bb["length"]
                    seq = list(DOTATATE[:length].ljust(length, "A"))
                    n_mut = random.randint(1, 4)
                    for _ in range(n_mut):
                        pos = random.randint(0, length - 1)
                        if seq[pos] != "C":
                            seq[pos] = random.choice(amino_acids)

                    sequence = "".join(seq)
                    all_sequences.append({
                        "seq_id": f"bb{backbones.index(bb):02d}_seq{j:02d}",
                        "backbone_id": bb["id"],
                        "sequence": sequence,
                    })

            ok(f"{len(all_sequences)}媛??쒗???ㅺ퀎 (dry-run)")
            for s in all_sequences[:3]:
                info(f"{s['seq_id']}: {s['sequence']}")
            info(f"... +{len(all_sequences) - 3} more sequences")
            emitter.complete_step("step03", t_step03)

        # ===============================================================
        # STEP 4: ESMFold QC (LIVE API!)
        # ===============================================================
        step_h("STEP 04", f"ESMFold - 援ъ“ ?덉륫 + pLDDT QC ({BOLD}{GREEN}LIVE API{RESET})")
        t_step04 = emitter.start_step("step04")

        # DOTATATE ?먮낯 ?쒗?ㅻ? 留??욎뿉 異붽? (寃利앹슜 control)
        dotatate_entry = {"seq_id": "DOTATATE_ref", "backbone_id": "ref", "sequence": DOTATATE}
        fold_list = [dotatate_entry] + all_sequences[:7]

        n_to_fold = len(fold_list)
        print(f"    {YELLOW}ESMFold API ?몄텧 以?.. ({n_to_fold}媛??쒗?? pLDDT gate >= {plddt_threshold}){RESET}")

        for i, seq_data in enumerate(fold_list):
            seq = seq_data["sequence"]
            if i > 0:
                time.sleep(1.5)  # rate-limit 諛⑹?
            t0 = time.time()
            result = esmfold_predict(seq)
            elapsed = time.time() - t0

            if result and "pdbs" in result:
                pdb_text = result["pdbs"] if isinstance(result["pdbs"], str) else result["pdbs"][0]
                plddts = extract_plddt_from_pdb(pdb_text)
                mean_plddt = sum(plddts) / len(plddts) if plddts else 0.0
                ca_plddts = plddts[::4] if len(plddts) > 4 else plddts  # Roughly CA atoms
                passed = mean_plddt >= plddt_threshold

                qc_results.append({
                    "seq_id": seq_data["seq_id"],
                    "sequence": seq,
                    "plddt_mean": round(mean_plddt, 1),
                    "plddt_min": round(min(plddts), 1) if plddts else 0,
                    "plddt_max": round(max(plddts), 1) if plddts else 0,
                    "n_atoms": len(plddts),
                    "pdb_lines": len(pdb_text.splitlines()),
                    "passed": passed,
                    "elapsed": elapsed,
                    "pdb": pdb_text,
                })

                # Persist ESMFold PDB for downstream Rosetta input
                if pdb_text:
                    qc_pdb_dir = Path("runs/live_run_001/04_qc")
                    qc_pdb_dir.mkdir(parents=True, exist_ok=True)
                    pdb_path = qc_pdb_dir / f"{seq_data['seq_id']}_esmfold.pdb"
                    pdb_path.write_text(pdb_text, encoding="utf-8")
                    qc_results[-1]["pdb_path"] = str(pdb_path)

                gate = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
                print(f"    {GREEN}[OK]{RESET} {seq_data['seq_id']:15s} | "
                      f"pLDDT={mean_plddt:>5.1f} (min={min(plddts):.0f} max={max(plddts):.0f}) | "
                      f"{len(plddts)} atoms | {gate} | {elapsed:.1f}s")
            else:
                qc_results.append({
                    "seq_id": seq_data["seq_id"], "sequence": seq,
                    "plddt_mean": 0, "passed": False, "elapsed": elapsed, "pdb": "",
                })
                fail(f"{seq_data['seq_id']}: ESMFold ?ㅽ뙣 ({elapsed:.1f}s)")

        n_passed = sum(1 for r in qc_results if r["passed"])
        n_failed = len(qc_results) - n_passed
        print(f"\n    {BOLD}QC Gate: {GREEN}{n_passed} passed{RESET} / {RED}{n_failed} failed{RESET} "
              f"(pLDDT >= {plddt_threshold})")
        emitter.complete_step("step04", t_step04)
        qc_gates_list = []
        if approach_b_enabled:
            qc_gates_list.append({
                "name": "Gate 0", "criterion": f"Stability >= {approach_b_cfg.get('stability_prescreen_min_hours', 50.0)}h",
                "passed": len(passed_prescreen), "failed": len(failed_prescreen),
                "total": step03b_output.total_generated,
            })
        qc_gates_list.append({
            "name": "Gate 1", "criterion": f"pLDDT >= {plddt_threshold}",
            "passed": n_passed, "failed": n_failed, "total": len(qc_results),
        })
        emitter.set_qc_gates(qc_gates_list)

        # ===============================================================
        # STEP 5: Docking scores (simulated with pLDDT-correlated mock)
        # ===============================================================
        step_h("STEP 05", "DiffDock - 遺꾩옄 ?꾪궧 (pLDDT 湲곕컲 ?쒕??덉씠??")
        t_step05 = emitter.start_step("step05")

        passed_qc = [r for r in qc_results if r["passed"]]
        for r in passed_qc:
            random.seed(hash(r["seq_id"]) % 2**32)
            # Dock score correlates with pLDDT (higher pLDDT -> more negative dock score)
            base_score = -(r["plddt_mean"] / 10.0) + random.gauss(0, 1.0)
            dock_results.append({
                "seq_id": r["seq_id"],
                "dock_score": round(base_score, 2),
                "confidence": round(random.uniform(0.6, 0.95), 2),
            })

        dock_results.sort(key=lambda x: x["dock_score"])
        ok(f"{len(dock_results)}媛??꾨낫 ?꾪궧 ?꾨즺")
        for dr in dock_results[:5]:
            info(f"{dr['seq_id']:15s} dock_score={dr['dock_score']:>7.2f}  conf={dr['confidence']:.2f}")
        emitter.complete_step("step05", t_step05)

        # Step 05b moved after Step 06 (needs refined PDB + SSTR2 ddG)
        n_sel_pass = 0

        # ===============================================================
        # STEP 6: Rosetta ddG (Real PyRosetta or Simulation Fallback)
        # ===============================================================
        pyrosetta_available = rosetta_enabled and is_pyrosetta_available(
            rosetta_cfg.get("conda_env", "bio-tools")
        )

        if pyrosetta_available:
            step_h("STEP 06", f"PyRosetta FlexPepDock - ddG 怨꾩궛 ({BOLD}{GREEN}LIVE PyRosetta{RESET})")
        else:
            step_h("STEP 06", f"PyRosetta FlexPepDock - ddG 怨꾩궛 ({YELLOW}?쒕??덉씠??fallback{RESET})")
        t_step06 = emitter.start_step("step06")

        if pyrosetta_available:
            est_minutes = min(rosetta_top_m, len(dock_results)) * 10
            info(f"PyRosetta ?ㅽ뻾 以?.. (?덉긽 ~{est_minutes}遺? {min(rosetta_top_m, len(dock_results))}媛??꾨낫)")

        if pyrosetta_available:
            from AG_src.pipeline.step06_rosetta import run_rosetta_refinement
            from AG_src.schemas.io_schemas import DockingResult

            # Convert dock_results dicts -> DockingResult dataclass
            dock_candidates = []
            for idx, dr in enumerate(dock_results[:rosetta_top_m]):
                qr_match = next((q for q in qc_results if q["seq_id"] == dr["seq_id"]), {})
                dock_candidates.append(DockingResult(
                    seq_id=dr["seq_id"],
                    engine="diffdock",
                    score=dr["dock_score"],
                    confidence=dr.get("confidence", 0.0),
                    pose_pdb=qr_match.get("pdb_path", ""),
                    rank=idx + 1,
                ))

            # Receptor PDB path
            receptor_pdb = str(Path(__file__).parent / "PRST_N_FM" / "results" / "sstr2_docking" / "sstr2_receptor.pdb")
            if not Path(receptor_pdb).exists():
                receptor_pdb = str(Path(__file__).parent / "PRST_N_FM" / "data" / "fold_test1" / "fold_test1_model_0.pdb")

            # Build seq_id -> sequence map for MutateResidue approach
            sequence_map = {}
            for q in qc_results:
                if "seq_id" in q and "sequence" in q:
                    sequence_map[q["seq_id"]] = q["sequence"]

            step06_config = {
                "run_id": run_id,
                "output_base_dir": str(Path(__file__).parent / "runs"),
                "gate_thresholds": {
                    "rosetta_ddg_max": float(gate_cfg.get("rosetta_ddg_max", -5.0)),
                    "rosetta_clash_max": int(gate_cfg.get("rosetta_clash_max", 5)),
                },
                "iteration": {
                    "top_m_rosetta": rosetta_top_m,
                },
                "rosetta": rosetta_cfg,
                "sequence_map": sequence_map,
            }

            # Optional FastRelax pre-step (energy minimization before docking)
            fast_relax_enabled = rosetta_cfg.get("fast_relax_before_dock", False)
            if fast_relax_enabled:
                step_h("STEP 06a", f"PyRosetta FastRelax - ?먮꼫吏 理쒖냼??({BOLD}{GREEN}LIVE{RESET})")
                info(f"FastRelax: {len(dock_candidates)}媛??꾨낫 ?먮꼫吏 理쒖냼??以?..")
                for dc in dock_candidates:
                    if dc.pose_pdb and Path(dc.pose_pdb).exists():
                        import subprocess as _sp
                        relax_out = Path(dc.pose_pdb).with_suffix(".relaxed.pdb")
                        relax_cmd = [
                            "conda", "run", "-n", rosetta_cfg.get("conda_env", "bio-tools"),
                            "python", str(Path(__file__).parent / "AG_src" / "scripts" / "fast_design.py"),
                            "--input", dc.pose_pdb,
                            "--output", str(relax_out),
                            "--protocol", "fast_relax",
                        ]
                        try:
                            relax_proc = _sp.run(relax_cmd, capture_output=True, text=True, timeout=600)
                            if relax_proc.returncode == 0 and relax_out.exists():
                                dc = dc._replace(pose_pdb=str(relax_out)) if hasattr(dc, '_replace') else dc
                                ok(f"FastRelax ?꾨즺: {dc.seq_id}")
                            else:
                                info(f"FastRelax 嫄대꼫?: {dc.seq_id} (returncode={relax_proc.returncode})")
                        except Exception as relax_exc:
                            info(f"FastRelax ?ㅽ뙣: {dc.seq_id} ({relax_exc})")

            try:
                info(f"PyRosetta ?ㅽ뻾 以?.. ({len(dock_candidates)}媛??꾨낫, receptor: {Path(receptor_pdb).name})")
                step06_output = run_rosetta_refinement(dock_candidates, receptor_pdb, step06_config)
                for rr in step06_output.rosetta_results:
                    rosetta_results.append({
                        "seq_id": rr.seq_id,
                        "ddg": round(rr.ddg, 1),
                        "clash": int(rr.clash_score),
                        "total_score": round(rr.total_score, 2),
                        "pre_score": round(rr.pre_score, 2),
                        "score_delta": round(rr.score_delta, 2),
                        "constraint_violations": rr.constraint_violations,
                        "refined_pdb": rr.refined_pdb,
                    })
                ok(f"PyRosetta ?ㅼ젣 ddG 怨꾩궛 ?꾨즺 ({len(rosetta_results)}媛?")
            except Exception as e:
                fail(f"PyRosetta ?ㅽ뻾 ?ㅽ뙣: {e}")
                if rosetta_fallback:
                    info("?쒕??덉씠??fallback?쇰줈 ?꾪솚...")
                    pyrosetta_available = False
                else:
                    emitter.fail_step("step06", t_step06)
                    raise

        if not pyrosetta_available:
            # Simulation fallback (original logic)
            for dr in dock_results[:rosetta_top_m]:
                random.seed(hash(dr["seq_id"] + "ros") % 2**32)
                ddg = dr["dock_score"] * 0.8 + random.gauss(0, 1.5)
                rosetta_results.append({
                    "seq_id": dr["seq_id"],
                    "ddg": round(ddg, 1),
                    "clash": random.choice([0, 0, 0, 1]),
                    "total_score": 0.0,
                    "constraint_violations": 0,
                    "refined_pdb": "",
                })
            info("(?쒕??덉씠??紐⑤뱶: PyRosetta 誘몄꽕移??먮뒗 鍮꾪솢?깊솕)")

        for rr in rosetta_results:
            gate_pass = rr["ddg"] <= rosetta_ddg_max and rr["clash"] <= rosetta_clash_max
            gate = f"{GREEN}PASS{RESET}" if gate_pass else f"{RED}FAIL{RESET}"
            delta_str = f"  delta={rr['score_delta']:>8.1f}" if rr.get("score_delta") is not None else ""
            score_str = f"  score={rr['total_score']:>8.1f}" if rr.get("total_score") else ""
            info(f"{rr['seq_id']:15s} ddG={rr['ddg']:>6.1f}  clash={rr['clash']}{score_str}{delta_str}  {gate}")

        n_ros_pass = sum(1 for r in rosetta_results if r["ddg"] <= rosetta_ddg_max and r["clash"] <= rosetta_clash_max)
        rosetta_mode_label = "LIVE" if pyrosetta_available else "simulated"
        ok(f"Rosetta 寃뚯씠?? {n_ros_pass}/{len(rosetta_results)} ?듦낵 (ddG<=-5.0, {rosetta_mode_label})")
        emitter.complete_step("step06", t_step06)

        # ===============================================================
        # STEP 5b: Real Selectivity Screening (PyRosetta off-target docking)
        # Moved after Step 06 to use refined PDB + SSTR2 ddG
        # ===============================================================
        sel_margin_min = float(gate_cfg.get("selectivity_margin_min", 10.0))   # G-2: 양수=좋음
        sel_ot_max = float(gate_cfg.get("offtarget_max_allowed", -15.0))

        if pyrosetta_available and rosetta_results and any(r.get("refined_pdb") for r in rosetta_results):
            step_h("STEP 05b", f"?좏깮???ㅽ겕由щ떇 - PyRosetta off-target ?꾪궧 ({BOLD}{GREEN}SSTR1/3/4/5{RESET})")
            t_step05b = emitter.start_step("step05b")

            # 1. Download AlphaFold structures for off-targets
            from AG_src.scripts.download_alphafold import download_alphafold_structure
            from AG_src.pipeline.step05b_selectivity import _run_offtarget_pyrosetta

            run_dir = Path(__file__).parent / "runs" / "live_run_001"
            offtarget_dir = run_dir / "01_receptor" / "offtargets"
            offtarget_dir.mkdir(parents=True, exist_ok=True)

            offtarget_receptors_live = []
            for ot_cfg in pipeline_cfg.get("off_target_receptors", []):
                try:
                    pdb_path = download_alphafold_structure(ot_cfg["uniprot_id"], str(offtarget_dir))
                    info(f"  {ot_cfg['name']}: {Path(pdb_path).name}")
                    offtarget_receptors_live.append({
                        "name": ot_cfg["name"],
                        "pdb_path": pdb_path,
                        "chain": ot_cfg.get("chain", "A"),
                    })
                except Exception as dl_exc:
                    fail(f"  {ot_cfg['name']}: AlphaFold ?ㅼ슫濡쒕뱶 ?ㅽ뙣 ({dl_exc})")

            # 2. Build seq_id -> refined SSTR2 complex PDB map
            sstr2_complex_pdbs = {}
            for rr in rosetta_results:
                if rr.get("refined_pdb") and Path(rr["refined_pdb"]).exists():
                    sstr2_complex_pdbs[rr["seq_id"]] = rr["refined_pdb"]

            # 3. Run real off-target docking
            ot_timeout = int(pipeline_cfg.get("selectivity", {}).get("offtarget_timeout_sec", 300))
            ot_conda_env = rosetta_cfg.get("conda_env", "bio-tools")

            for dr in dock_results[:5]:
                sid = dr["seq_id"]
                sstr2_ddg = next((r["ddg"] for r in rosetta_results if r["seq_id"] == sid), 0.0)
                sstr2_pdb = sstr2_complex_pdbs.get(sid, "")
                ot_scores = {}

                for ot in offtarget_receptors_live:
                    if sstr2_pdb:
                        try:
                            ot_ddg = _run_offtarget_pyrosetta(
                                sstr2_pdb, ot["pdb_path"],
                                timeout=ot_timeout, conda_env=ot_conda_env,
                            )
                        except Exception as dock_exc:
                            info(f"  {sid} vs {ot['name']}: dock failed ({dock_exc}), estimation fallback")
                            ot_ddg = sstr2_ddg + random.gauss(15.0, 3.0)
                    else:
                        ot_ddg = sstr2_ddg + random.gauss(15.0, 3.0)
                    ot_scores[ot["name"]] = round(ot_ddg, 2)

                # margin = worst_OT_ddG - SSTR2_ddG (G-2 SSOT: 양수=좋음, more positive = SSTR2 binds stronger)
                worst_ot = min(ot_scores.values()) if ot_scores else 0.0
                margin = worst_ot - sstr2_ddg

                sel = SelectivityResult(
                    seq_id=sid,
                    sstr2_dock_score=sstr2_ddg,
                    offtarget_scores=ot_scores,
                    offtarget_max_score=worst_ot,
                    offtarget_max_receptor=min(ot_scores, key=ot_scores.get) if ot_scores else "none",
                    selectivity_margin=margin,
                    passed=(margin >= sel_margin_min),
                )
                sel_results.append(sel)
                gate = f"{GREEN}PASS{RESET}" if sel.passed else f"{RED}FAIL{RESET}"
                info(f"{sid:15s} SSTR2_ddG={sstr2_ddg:>7.1f}  worst_OT={worst_ot:>7.1f}  margin={margin:>7.1f}  {gate}")

            n_sel_pass = sum(1 for r in sel_results if r.passed)
            ok(f"?좏깮??寃뚯씠?? {n_sel_pass}/{len(sel_results)} ?듦낵 (PyRosetta off-target)")
            emitter.complete_step("step05b", t_step05b)
        else:
            # Fallback: estimation mode (no refined PDB available)
            step_h("STEP 05b", "?좏깮???ㅽ겕由щ떇 (異붿젙 紐⑤뱶 - refined PDB ?놁쓬)")
            t_step05b = emitter.start_step("step05b")
            for dr in dock_results[:5]:
                random.seed(hash(dr["seq_id"] + "sel") % 2**32)
                sstr2_ddg = next((r["ddg"] for r in rosetta_results if r["seq_id"] == dr["seq_id"]), dr["dock_score"])
                ot = {
                    "SSTR1": sstr2_ddg + random.gauss(15.0, 3.0),
                    "SSTR3": sstr2_ddg + random.gauss(18.0, 4.0),
                    "SSTR4": sstr2_ddg + random.gauss(20.0, 3.5),
                    "SSTR5": sstr2_ddg + random.gauss(12.0, 3.0),
                }
                sel = compute_selectivity_margin(
                    seq_id=dr["seq_id"], sstr2_score=sstr2_ddg,
                    offtarget_scores=ot, margin_min=sel_margin_min, offtarget_max_allowed=sel_ot_max,
                )
                sel_results.append(sel)
                gate = f"{GREEN}PASS{RESET}" if sel.passed else f"{RED}FAIL{RESET}"
                info(f"{sel.seq_id:15s} SSTR2={sstr2_ddg:>7.1f}  margin={sel.selectivity_margin:>7.1f}  {gate}")

            n_sel_pass = sum(1 for r in sel_results if r.passed)
            ok(f"?좏깮??寃뚯씠?? {n_sel_pass}/{len(sel_results)} ?듦낵 (異붿젙 紐⑤뱶)")
            emitter.complete_step("step05b", t_step05b)

        # Update QC gates with all results
        qc_gates_final = []
        if approach_b_enabled:
            qc_gates_final.append({
                "name": "Gate 0", "criterion": f"Stability >= {approach_b_cfg.get('stability_prescreen_min_hours', 50.0)}h",
                "passed": len(passed_prescreen), "failed": len(failed_prescreen),
                "total": step03b_output.total_generated,
            })
        qc_gates_final.extend([
            {"name": "Gate 1", "criterion": f"pLDDT >= {plddt_threshold}", "passed": n_passed, "failed": n_failed, "total": len(qc_results)},
            {"name": "Gate 2", "criterion": "Top 20% Docking", "passed": len(dock_results), "failed": len(passed_qc) - len(dock_results), "total": len(passed_qc)},
            {"name": "Gate 3", "criterion": f"ddG <= {rosetta_ddg_max} & clash <= {rosetta_clash_max}", "passed": n_ros_pass, "failed": len(rosetta_results) - n_ros_pass, "total": len(rosetta_results)},
            {"name": "Gate 4", "criterion": f"Selectivity margin >= {sel_margin_min}", "passed": n_sel_pass, "failed": len(sel_results) - n_sel_pass, "total": len(sel_results)},
        ])
        emitter.set_qc_gates(qc_gates_final)

        # ===============================================================
        # STEP 7: Analysis & Visualization (FoldMason + PyMOL)
        # ===============================================================
        step07_lddt_scores: Dict[str, float] = {}
        if pyrosetta_available and rosetta_results and any(r.get("refined_pdb") for r in rosetta_results):
            step_h("STEP 07", f"援ъ“ 遺꾩꽍 & ?쒓컖??({BOLD}{CYAN}FoldMason + PyMOL{RESET})")
            t_step07 = emitter.start_step("step07")
            try:
                from AG_src.pipeline.step07_analysis import run_analysis
                from AG_src.schemas.io_schemas import RosettaResult as RosettaResultSchema

                rosetta_objs = [
                    RosettaResultSchema(
                        seq_id=rr["seq_id"], ddg=rr["ddg"],
                        total_score=rr.get("total_score", 0.0),
                        clash_score=float(rr.get("clash", 0)),
                        constraint_violations=rr.get("constraint_violations", 0),
                        refined_pdb=rr.get("refined_pdb", ""),
                    )
                    for rr in rosetta_results if rr.get("refined_pdb")
                ]

                step07_config = {
                    "run_id": run_id,
                    "output_base_dir": str(Path(__file__).parent / "runs"),
                }
                step07_output = run_analysis(rosetta_objs, receptor_pdb, step07_config)

                if step07_output.lddt_table_path and Path(step07_output.lddt_table_path).exists():
                    fm_data = json.loads(Path(step07_output.lddt_table_path).read_text())
                    step07_lddt_scores = fm_data.get("lddt_scores", {})

                ok("援ъ“ 遺꾩꽍 ?꾨즺")
                if step07_output.rank_table_csv:
                    info(f"?쒖쐞 ?뚯씠釉? {step07_output.rank_table_csv}")
                if step07_output.summary_md:
                    info(f"?붿빟 蹂닿퀬?? {step07_output.summary_md}")
                if step07_output.pymol_renders:
                    ok(f"PyMOL ?뚮뜑: {list(step07_output.pymol_renders.keys())}")
                else:
                    info("PyMOL 誘몄꽕移? ?뚮뜑 嫄대꼫?")
                emitter.complete_step("step07", t_step07)

                # Emit visualization images for dashboard
                viz_dir = run_dir / "07_viz"
                runs_base = Path(__file__).parent / "runs"
                viz_images = []
                for img_type in ["overview", "closeup", "interface", "electrostatics"]:
                    img_path = viz_dir / f"{img_type}.png"
                    if img_path.exists():
                        rel_path = img_path.relative_to(runs_base)
                        viz_images.append({
                            "label": img_type.capitalize(),
                            "url": f"/api/images/{rel_path}",
                            "type": img_type,
                        })
                if viz_images:
                    emitter.set_visualization_images(viz_images)
            except Exception as exc:
                fail(f"Step07 遺꾩꽍 ?ㅽ뙣 (鍮꾪븘???④퀎, 怨꾩냽 吏꾪뻾): {exc}")
                emitter.fail_step("step07", t_step07)
        else:
            emitter.update_step("step07", "skipped")

        # Build candidate list for dashboard
        _dashboard_candidates = []
        for rank_i, dr in enumerate(dock_results[:10]):
            sid = dr["seq_id"]
            qr_match = next((q for q in qc_results if q["seq_id"] == sid), {})
            ros_match = next((r for r in rosetta_results if r["seq_id"] == sid), {})
            sel_match = next((s for s in sel_results if s.seq_id == sid), None)
            _dashboard_candidates.append({
                "rank": rank_i + 1,
                "id": sid,
                "sequence": qr_match.get("sequence", ""),
                "pLDDT": qr_match.get("plddt_mean", 0),
                "dockScore": dr["dock_score"],
                "ddG": ros_match.get("ddg", 0),
                "lDDT": step07_lddt_scores.get(sid, round(random.uniform(0.55, 0.9), 3)),
                "selectivity": round(sel_match.selectivity_margin, 2) if sel_match else 0,
                "finalScore": round(compute_final_score(
                    plddt=qr_match.get("plddt_mean", 0),
                    dock_score=dr.get("dock_score", 0) if dr else 0,
                    ddg=ros_match.get("ddg", 0),
                    lddt=step07_lddt_scores.get(sid, 0),
                    selectivity_margin=sel_match.selectivity_margin if sel_match else 0,
                ), 3),
                "result": "PASS" if (qr_match.get("passed") and ros_match.get("ddg", 0) <= -5.0) else "FAIL",
            })
        emitter.set_candidates(_dashboard_candidates)

        # ===============================================================
        # AGENTS: Run all 5 agents
        # ===============================================================
        step_h("AGENTS", f"5媛??먯씠?꾪듃 ?ㅽ뻾 - Iteration {current_iteration} (Planner ??QCRanker ??DiversityMgr ??Critic ??Reporter)")

        # --- Planner ---
        agent_h("Planner")
        emitter.update_agent("planner", status="active", message=f"Generating experiment plan (iter {current_iteration})...")
        t0 = time.time()
        planner = PlannerAgent(llm_provider=llm)
        plan_result = planner.execute({
            "receptor_config": {"name": "SSTR2", "chain": "B"},
            "constraints": {"n_backbone": 5, "k_seq_per_backbone": 4},
            "iteration": current_iteration,
        })
        ok(f"?ㅽ뿕 怨꾪쉷 ?앹꽦 ({time.time()-t0:.3f}s)")
        plan = plan_result.get("plan")
        if plan:
            info(f"Run ID: {plan.run_id}")
            info(f"Hypothesis: {plan.hypothesis[:80]}...")
            emitter.update_agent("planner", status="idle", message=f"Plan ready: {plan.hypothesis[:60]}...", task_count_delta=1,
                report={
                    "type": "plan",
                    "run_id": plan.run_id,
                    "hypothesis": plan.hypothesis,
                    "strategy": plan.strategy if hasattr(plan, "strategy") else "",
                    "iteration": current_iteration,
                })

        # --- QCRanker ---
        agent_h("QCRanker")
        emitter.update_agent("qc-ranker", status="active", message="Running multi-gate QC ranking...")
        candidates = []
        # Build lookup maps from pipeline results
        dock_map = {d["seq_id"]: d for d in dock_results}
        ros_map = {r["seq_id"]: r for r in rosetta_results}
        sel_map = {s.seq_id: s for s in sel_results}

        for r in qc_results:
            if r.get("plddt_mean", 0) <= 0:
                continue
            sid = r["seq_id"]
            # Parse bb{XX}_seq{YY} pattern; skip non-standard ids like DOTATATE_ref
            try:
                bb_id = int(sid[2:4])
                s_id = int(sid[-2:])
            except (ValueError, IndexError):
                bb_id, s_id = 99, 99

            dock_data = dock_map.get(sid, {})
            ros_data = ros_map.get(sid, {})
            sel_data = sel_map.get(sid, None)

            candidates.append(Candidate(
                candidate_id=sid,
                backbone_id=bb_id,
                seq_id=s_id,
                sequence=r.get("sequence", ""),
                plddt_mean=r.get("plddt_mean", 0.0),
                plddt_interface=r.get("plddt_mean", 0.0) * 0.85,  # approximate interface pLDDT
                dock_score=dock_data.get("dock_score", 0.0),
                ddg=ros_data.get("ddg", 0.0),
                clash_count=ros_data.get("clash", 0),
                constraint_violations=ros_data.get("constraint_violations", 0),
                selectivity_margin=sel_data.selectivity_margin if sel_data else 0.0,
            ))
        t0 = time.time()
        qcranker = QCRankerAgent(llm_provider=llm)
        qc_rank_result = qcranker.execute({
            "candidates": candidates,
            "thresholds": gate_cfg,
            "run_id": run_id,
            "iteration": current_iteration,
        })
        ok(f"QC ??궧 ?꾨즺 ({time.time()-t0:.3f}s)")
        rt = qc_rank_result.get("rank_table")
        qr = qc_rank_result.get("qc_report")
        if rt:
            info(f"Ranked: {len(rt.ranked_candidates)} candidates")
        if qr:
            info(f"Pass rate: {qr.passed_count}/{qr.total_input} ({qr.pass_rate:.1%})")
            emitter.update_agent("qc-ranker", status="idle", message=f"Pass rate: {qr.passed_count}/{qr.total_input}", task_count_delta=1)

        # --- DiversityManager ---
        agent_h("DiversityManager")
        emitter.update_agent("diversity-mgr", status="active", message="Analyzing sequence diversity...")
        t0 = time.time()
        divmgr = DiversityManagerAgent(llm_provider=llm)
        div_result = divmgr.execute({"candidates": candidates[:8], "n_select": 5, "method": "foldmason"})
        ok(f"?ㅼ뼇???꾪꽣 ({time.time()-t0:.3f}s)")
        info(f"Clusters: {len(div_result.get('clusters', []))}")
        info(f"Selected: {len(div_result.get('diverse_candidates', []))}")
        emitter.update_agent("diversity-mgr", status="idle", message=f"{len(div_result.get('clusters',[]))} clusters found", task_count_delta=1)

        # --- Critic ---
        agent_h("ScientistCritic")
        emitter.update_agent("critic", status="active", message=f"Reviewing iteration {current_iteration} results...")
        t0 = time.time()
        critic = ScientistCriticAgent(llm_provider=llm)
        critic_result = critic.execute({
            "rank_table": rt, "qc_report": qr, "iteration": current_iteration,
            "current_params": {"n_backbone": 5, "k_seq_per_backbone": 4},
        })
        ok(f"鍮꾪룊 遺꾩꽍 ({time.time()-t0:.3f}s)")
        analysis = critic_result.get("critic_analysis")
        if analysis:
            info(f"Hypothesis: {analysis.hypothesis[:80]}...")
            info(f"Changes: {len(analysis.proposed_changes)}")
            emitter.update_agent("critic", status="idle", message=f"{len(analysis.proposed_changes)} changes proposed", task_count_delta=1,
                report={
                    "type": "critic",
                    "hypothesis": analysis.hypothesis,
                    "proposed_changes": [
                        {"parameter": c.parameter_name, "old": str(c.old_value),
                         "new": str(c.new_value), "rationale": c.rationale}
                        for c in analysis.proposed_changes
                    ],
                    "iteration": current_iteration,
                })

        # --- Reporter ---
        agent_h("Reporter")
        emitter.update_agent("reporter", status="active", message=f"Generating lab notebook (iter {current_iteration})...")
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            t0 = time.time()
            reporter = ReporterAgent(runs_base_dir=tmpdir, llm_provider=llm)
            report_result = reporter.execute({
                "run_id": f"live_demo_iter{current_iteration:02d}", "iteration": current_iteration,
                "rank_table": rt, "top_candidates": candidates[:5],
                "receptor_pdb": "/tmp/sstr2.pdb",
                "output_dir": str(Path(tmpdir) / "reports"),
            })
            ok(f"蹂닿퀬???앹꽦 ({time.time()-t0:.3f}s)")
            for name, path in report_result.get("report_paths", {}).items():
                info(f"{name}: .../{Path(path).name}")
            _summary_path = report_result.get("report_paths", {}).get("summary_md", "")
            _summary_content = ""
            if _summary_path:
                try:
                    _summary_content = Path(_summary_path).read_text(encoding="utf-8")
                except Exception:
                    pass
            emitter.update_agent("reporter", status="idle", message="Reports generated", task_count_delta=1,
                report={
                    "type": "reporter",
                    "summary": _summary_content,
                    "iteration": current_iteration,
                })

        # ===============================================================
        # CONVERGENCE CHECK
        # ===============================================================
        # Collect this iteration's best candidates
        iter_best = [r for r in rosetta_results if r["ddg"] <= conv_ddg_thresh]
        all_candidates_history.extend(iter_best)

        best_ddg = min((r["ddg"] for r in rosetta_results), default=0.0)

        convergence_log.append({
            "iteration": current_iteration,
            "bestDdG": best_ddg,
            "topCandidates": len(iter_best),
            "converged": False,
        })

        # Update per-iteration tracking for final summary
        final_qc_results = qc_results
        final_dock_results = dock_results
        final_rosetta_results = rosetta_results
        final_sel_results = sel_results
        final_n_passed = n_passed
        final_n_failed = n_failed
        final_n_ros_pass = n_ros_pass
        final_n_sel_pass = n_sel_pass
        final_n_to_fold = n_to_fold

        # Check convergence (adaptive mode)
        if adaptive and current_iteration >= min_iterations:
            # Criterion 1: Enough good candidates accumulated
            total_good = len([c for c in all_candidates_history if c["ddg"] <= conv_ddg_thresh])
            if total_good >= conv_min_cands:
                print(f"\n    {GREEN}CONVERGED: {total_good} candidates with ddG <= {conv_ddg_thresh}{RESET}")
                convergence_log[-1]["converged"] = True
                break

            # Criterion 2: No improvement patience
            if best_ddg >= prev_best_ddg and current_iteration > 1:
                no_improvement_count += 1
            else:
                no_improvement_count = 0

            if no_improvement_count >= patience:
                print(f"\n    {YELLOW}EARLY STOP: No improvement for {patience} iterations{RESET}")
                convergence_log[-1]["converged"] = True
                break

            prev_best_ddg = min(best_ddg, prev_best_ddg) if prev_best_ddg != 0.0 else best_ddg

        # Apply Critic suggestions for next iteration (if available)
        if critic_result and current_iteration < max_iterations:
            crit_analysis = critic_result.get("critic_analysis")
            if crit_analysis and crit_analysis.proposed_changes:
                for change in crit_analysis.proposed_changes:
                    print(f"    {YELLOW}Critic: {change}{RESET}")

    # === END OF ITERATION LOOP ===

    # Set best candidate from final iteration
    if final_qc_results:
        best = max(final_qc_results, key=lambda x: x.get("plddt_mean", 0))
        best_dock = next((d for d in final_dock_results if d["seq_id"] == best["seq_id"]), None)
        emitter.set_best_candidate({
            "id": best["seq_id"],
            "sequence": best["sequence"],
            "plddt": best["plddt_mean"],
            "dockScore": best_dock["dock_score"] if best_dock else None,
        })

    # Emit all convergence points from the log
    for cp in convergence_log:
        emitter.add_convergence_point(
            iteration=cp["iteration"],
            best_ddg=cp["bestDdG"],
            top_candidates=cp["topCandidates"],
            converged=cp["converged"],
        )

    # ===================================================================
    # STEP 8: GLP-1 Stability (runs ONCE after all iterations)
    # ===================================================================
    step_h("STEP 08", "GLP-1 ?덉젙???덉륫")
    t_step08 = emitter.start_step("step08")

    from AG_src.pipeline.step08_stability import run_stability_evaluation

    stab_candidates = [{"candidate_id": r["seq_id"], "sequence": next(
        q["sequence"] for q in final_qc_results if q["seq_id"] == r["seq_id"]
    ), "modifications": []} for r in final_dock_results[:5]]

    report = run_stability_evaluation(stab_candidates)
    for sr in report.results:
        gate = f"{GREEN}PASS{RESET}" if sr.target_met else f"{RED}FAIL{RESET}"
        info(f"{sr.candidate_id:15s} {sr.base_half_life_hours:>5.1f}h ??{sr.modified_half_life_hours:>6.1f}h  {gate}")
        if sr.modifications[:1]:
            m = sr.modifications[0]
            info(f"  ?붴? Best: {m.mod_type} at {m.original}{m.position} (+{m.half_life_gain_hours:.0f}h)")
    ok(f"?덉젙??寃뚯씠?? {report.n_passed}/{len(report.results)} ?듦낵 (>={report.min_half_life}h)")
    emitter.complete_step("step08", t_step08)

    # ===================================================================
    # STEP 9: MolMIM molecular optimization (LIVE API!) - runs ONCE
    # ===================================================================
    step_h("STEP 09", f"MolMIM - 遺꾩옄 理쒖쟻??({BOLD}{GREEN}LIVE API{RESET})")
    t_step09 = emitter.start_step("step09")

    # Generate optimized variants of DOTATATE-like SMILES
    dotatate_smiles = "CC(=O)NC(CS)C(=O)NC(CCCCN)C(=O)NC(CC1=CC=CC=C1)C(=O)O"
    info(f"Input SMILES: {dotatate_smiles[:50]}...")

    t0 = time.time()
    molmim_result = molmim_generate(dotatate_smiles, n=5)
    elapsed = time.time() - t0

    if molmim_result and "molecules" in molmim_result:
        molecules = molmim_result["molecules"]
        if isinstance(molecules, str):
            molecules = json.loads(molecules)
        ok(f"MolMIM: {len(molecules)}媛?遺꾩옄 ?앹꽦 ({elapsed:.2f}s)")
        mol_dashboard = []
        for i, mol in enumerate(molecules[:5]):
            smi = mol.get("sample", "?")
            score = mol.get("score", 0)
            info(f"mol_{i}: {smi[:50]}{'...' if len(smi)>50 else ''} (QED={score:.3f})")
            mol_dashboard.append({"id": f"mol_{i}", "smiles": smi, "qed": score})
        emitter.set_molecules(mol_dashboard)
        emitter.complete_step("step09", t_step09)
    else:
        fail(f"MolMIM ?몄텧 ?ㅽ뙣 ({elapsed:.2f}s)")
        emitter.fail_step("step09", t_step09)

    # Mark pipeline complete
    emitter.set_completed()

    # ===================================================================
    # FINAL SUMMARY
    # ===================================================================
    total_iterations_run = len(convergence_log)
    converged = any(cp["converged"] for cp in convergence_log)
    banner(f"Pipeline Complete! ({total_iterations_run} iteration{'s' if total_iterations_run > 1 else ''}"
           f"{', CONVERGED' if converged else ''})", char="*")

    print(f"  {BOLD}Iterations:{RESET}  {total_iterations_run}/{max_iterations}"
          f"  {'(converged)' if converged else '(max reached)'}")
    print(f"  {BOLD}Adaptive:{RESET}    {'ON' if adaptive else 'OFF'}")
    if convergence_log:
        for cp in convergence_log:
            tag = f"{GREEN}CONVERGED{RESET}" if cp["converged"] else f"{DIM}continue{RESET}"
            print(f"    Iter {cp['iteration']}: bestDdG={cp['bestDdG']:.1f}  topCandidates={cp['topCandidates']}  {tag}")
    print()

    print(f"  {BOLD}Live API Calls:{RESET}")
    print(f"    {BG_GREEN}{WHITE} ESMFold {RESET}  {final_n_to_fold} sequences folded ??{final_n_passed}/{len(final_qc_results)} passed QC")
    if molmim_result:
        mols = molmim_result.get("molecules", "[]")
        n_mol = len(json.loads(mols)) if isinstance(mols, str) else len(mols)
        print(f"    {BG_GREEN}{WHITE} MolMIM  {RESET}  {n_mol} optimized molecules generated")

    if approach_b_enabled:
        print(f"\n  {BOLD}Approach B (BLOSUM62 Mutation):{RESET}")
        if step03b_output:
            print(f"    BLOSUM variants  ??{step03b_output.total_generated} generated ({n_singles} single + {n_combos} combo)")
            print(f"    Stability pre-screen ??{len(passed_prescreen)}/{step03b_output.total_generated} passed (>={prescreen_min_hours}h)")
        print(f"    ESMFold QC       ??{final_n_passed}/{len(final_qc_results)} passed pLDDT gate")
        print(f"    DiffDock         ??{len(final_dock_results)} docking scores (simulated)")
        print(f"    Selectivity      ??{final_n_sel_pass}/{len(final_sel_results)} SSTR2-selective")
        print(f"    PyRosetta        ??{final_n_ros_pass}/{len(final_rosetta_results)} passed ddG gate ({rosetta_mode_label})")
        print(f"    GLP-1 Stability  ??{report.n_passed}/{len(report.results)} passed (>={report.min_half_life}h)")
    else:
        print(f"\n  {BOLD}Simulated Steps:{RESET}")
        print(f"    RFdiffusion      ??{len(backbones)} backbones (dry-run)")
        print(f"    ProteinMPNN      ??{len(all_sequences)} sequences (dry-run)")
        print(f"    DiffDock         ??{len(final_dock_results)} docking scores (simulated)")
        print(f"    Selectivity      ??{final_n_sel_pass}/{len(final_sel_results)} SSTR2-selective")
        print(f"    PyRosetta        ??{final_n_ros_pass}/{len(final_rosetta_results)} passed ddG gate ({rosetta_mode_label})")
        print(f"    GLP-1 Stability  ??{report.n_passed}/{len(report.results)} passed (>={report.min_half_life}h)")

    print(f"\n  {BOLD}Agents (5/5):{RESET}")
    print(f"    {MAGENTA}Planner{RESET}          ??Experiment plan + hypothesis")
    print(f"    {GREEN}QCRanker{RESET}         ??Multi-gate ranking")
    print(f"    {CYAN}DiversityManager{RESET} ??Cluster-based selection")
    print(f"    {YELLOW}ScientistCritic{RESET}  ??Parameter optimization")
    print(f"    {BLUE}Reporter{RESET}         ??Lab notebook generation")

    # Show best candidate
    if final_qc_results:
        best = max(final_qc_results, key=lambda x: x.get("plddt_mean", 0))
        print(f"\n  {BOLD}Best Candidate:{RESET}")
        print(f"    ID:       {best['seq_id']}")
        print(f"    Sequence: {best['sequence']}")
        print(f"    pLDDT:    {best['plddt_mean']}")
        if any(dr["seq_id"] == best["seq_id"] for dr in final_dock_results):
            dr = next(d for d in final_dock_results if d["seq_id"] == best["seq_id"])
            print(f"    Docking:  {dr['dock_score']}")

    print(f"\n  {DIM}LLM: {llm}{RESET}\n")


if __name__ == "__main__":
    if not _run_pyrosetta_flow_if_requested():
        main()

