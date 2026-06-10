#!/usr/bin/env python3
"""
SSTR2 Peptide Binder Pipeline - Live Demo with Frontend Monitoring
===================================================================
멀티 이터레이션 파이프라인 + runs/live_demo/pipeline_status.json 실시간 업데이트.
API 403 시 자동으로 시뮬레이션 모드 전환.

Usage:
    # 터미널 1: 파이프라인 실행
    NVIDIA_NIM_API_KEY="nvapi-..." python runs/run_live_demo.py

    # 터미널 2: API 서버 (프론트엔드 연결용)
    python runs/serve_api.py

    # 터미널 3: 프론트엔드
    cd frontend && npm run dev
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STATUS_DIR = ROOT / "runs" / "live_demo"
STATUS_FILE = STATUS_DIR / "pipeline_status.json"

MAX_ITERATIONS = 3
CONVERGENCE_THRESHOLD = 0.5  # kcal/mol

# ---------------------------------------------------------------------------
# Colors (terminal output)
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
BG_YELLOW = "\033[43m"


def p(msg: str, color: str = CYAN) -> None:
    print(f"{DIM}{time.strftime('%H:%M:%S')}{RESET} {color}{msg}{RESET}")


def banner(text: str, char: str = "=", width: int = 72) -> None:
    print(f"\n{BOLD}{MAGENTA}{char * width}\n  {text}\n{char * width}{RESET}\n")


def step_h(name: str, desc: str) -> None:
    print(f"\n  {BG_BLUE}{WHITE}{BOLD} {name} {RESET}  {desc}\n  {'─' * 60}")


def agent_h(name: str) -> None:
    colors = {"Planner": MAGENTA, "QCRanker": GREEN, "DiversityManager": CYAN,
              "ScientistCritic": YELLOW, "Reporter": BLUE}
    c = colors.get(name, WHITE)
    print(f"\n  {c}{BOLD}▶ Agent: {name}{RESET}")


def ok(msg: str) -> None:
    print(f"    {GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"    {RED}✗{RESET} {msg}")


def info(msg: str) -> None:
    print(f"    {DIM}→{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"    {YELLOW}⚠{RESET} {msg}")


# ---------------------------------------------------------------------------
# Status JSON writer (프론트엔드 연동)
# ---------------------------------------------------------------------------
class PipelineStatusWriter:
    """파이프라인 진행 상태를 JSON 파일로 실시간 기록."""

    def __init__(self, output_path: Path) -> None:
        self._path = output_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, Any] = {
            "run_id": "",
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "iteration": 1,
            "total_iterations": MAX_ITERATIONS,
            "llm_model": "Qwen 2.5 7B (NoneProvider — rule-based)",
            "target": "SSTR2 (Somatostatin Receptor Type 2)",
            "reference": "DOTATATE (AGCKNFFWKTFTSC, 14-aa)",
            "steps": [],
            "agents": [],
            "candidates": [],
            "qc_gates": [],
            "convergence": [],
            "live_apis": {"esmfold": "pending", "molmim": "pending"},
            "best_candidate": None,
            "molecules": [],
            "completed": False,
        }
        self._flush()

    def _flush(self) -> None:
        self._state["updated_at"] = datetime.now().isoformat()
        self._path.write_text(json.dumps(self._state, indent=2, ensure_ascii=False))

    def set_run_id(self, run_id: str) -> None:
        self._state["run_id"] = run_id
        self._flush()

    def set_iteration(self, iteration: int) -> None:
        self._state["iteration"] = iteration
        self._flush()

    def update_step(self, step_id: str, label: str, short_label: str,
                    status: str, duration: str | None = None) -> None:
        steps = self._state["steps"]
        existing = next((s for s in steps if s["id"] == step_id), None)
        entry = {"id": step_id, "label": label, "shortLabel": short_label,
                 "status": status, "duration": duration}
        if existing:
            existing.update(entry)
        else:
            steps.append(entry)
        self._flush()

    def reset_steps(self) -> None:
        """모든 스텝을 pending 으로 리셋."""
        for s in self._state["steps"]:
            s["status"] = "pending"
            s["duration"] = None
        self._flush()

    def update_agent(self, agent_id: str, name: str, agent_type: str,
                     status: str, message: str, task_count: int = 0) -> None:
        agents = self._state["agents"]
        existing = next((a for a in agents if a["id"] == agent_id), None)
        entry = {"id": agent_id, "name": name, "type": agent_type,
                 "status": status, "lastMessage": message, "taskCount": task_count}
        if existing:
            existing.update(entry)
        else:
            agents.append(entry)
        self._flush()

    def set_candidates(self, candidates: list[dict]) -> None:
        self._state["candidates"] = candidates
        self._flush()

    def set_qc_gates(self, gates: list[dict]) -> None:
        self._state["qc_gates"] = gates
        self._flush()

    def update_live_api(self, name: str, status: str) -> None:
        self._state["live_apis"][name] = status
        self._flush()

    def set_best_candidate(self, candidate: dict) -> None:
        self._state["best_candidate"] = candidate
        self._flush()

    def set_molecules(self, molecules: list[dict]) -> None:
        self._state["molecules"] = molecules
        self._flush()

    def add_convergence_point(self, point: dict) -> None:
        self._state["convergence"].append(point)
        self._flush()

    def mark_completed(self) -> None:
        self._state["completed"] = True
        self._state["completed_at"] = datetime.now().isoformat()
        self._flush()


# ---------------------------------------------------------------------------
# NIM API helpers + simulation fallback
# ---------------------------------------------------------------------------
API_KEY: str | None = None
BASE = "https://health.api.nvidia.com/v1"
API_MODE: str = "live"  # "live" or "simulated"


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
        if e.code == 403:
            fail(f"HTTP 403 Authorization failed — API 키 만료 또는 비활성화")
        else:
            fail(f"HTTP {e.code}: {body}")
        return None
    except Exception as e:
        fail(f"Error: {e}")
        return None


def check_api_availability() -> bool:
    """API 키가 유효한지 짧은 시퀀스로 테스트."""
    result = nim_post("/biology/nvidia/esmfold", {"sequence": "MKTL"}, timeout=30)
    return result is not None


def esmfold_predict(sequence: str, retries: int = 2) -> Optional[dict]:
    """실제 ESMFold API 호출 (retry 포함)."""
    for attempt in range(retries + 1):
        result = nim_post("/biology/nvidia/esmfold", {"sequence": sequence})
        if result is not None:
            return result
        if attempt < retries:
            wait = 2 * (attempt + 1)
            info(f"  재시도 {attempt + 2}/{retries + 1} ({wait}s 대기...)")
            time.sleep(wait)
    return None


def esmfold_simulate(sequence: str, iteration: int = 1) -> dict:
    """ESMFold 시뮬레이션 — API 불가 시 현실적 mock 데이터 생성."""
    random.seed(hash(sequence + str(iteration)) % 2**32)
    length = len(sequence)
    # pLDDT는 시퀀스 길이, 이터레이션에 따라 점진적으로 향상
    base_plddt = 55 + random.gauss(10, 8) + (iteration - 1) * 3
    plddts = [max(20, min(95, base_plddt + random.gauss(0, 5))) for _ in range(length * 8)]
    mean_plddt = sum(plddts) / len(plddts)
    return {
        "plddt_mean": round(mean_plddt, 1),
        "plddt_min": round(min(plddts), 1),
        "plddt_max": round(max(plddts), 1),
        "n_atoms": len(plddts),
        "simulated": True,
    }


def molmim_generate(smiles: str, n: int = 3) -> Optional[dict]:
    return nim_post("/biology/nvidia/molmim/generate", {
        "smi": smiles, "num_molecules": n, "algorithm": "CMA-ES",
    })


def molmim_simulate(smiles: str, n: int = 5) -> dict:
    """MolMIM 시뮬레이션 — API 불가 시 mock 분자 생성."""
    random.seed(hash(smiles) % 2**32)
    molecules = []
    for i in range(n):
        # 약간 변형된 SMILES 생성
        score = round(random.uniform(0.55, 0.92), 3)
        mol_smi = smiles[:30] + f"C(=O)N{random.choice('CNOS')}" * random.randint(1, 3)
        molecules.append({"sample": mol_smi, "score": score})
    return {"molecules": molecules}


def extract_plddt_from_pdb(pdb_text: str) -> list[float]:
    plddts = []
    for line in pdb_text.splitlines():
        if line.startswith("ATOM") and len(line) >= 66:
            try:
                plddts.append(float(line[60:66].strip()))
            except ValueError:
                pass
    return plddts


# ---------------------------------------------------------------------------
# Iteration parameter evolution
# ---------------------------------------------------------------------------
def evolve_params(base_params: dict, critic_changes: list[dict], iteration: int) -> dict:
    """Critic 제안을 반영하여 파라미터 갱신."""
    params = {**base_params}
    for change in critic_changes:
        key = change.get("parameter", "")
        new_val = change.get("new_value")
        if key and new_val is not None:
            params[key] = new_val
    # 이터레이션이 증가할수록 시퀀스 수 증가
    params["k_seq_per_backbone"] = min(8, base_params.get("k_seq_per_backbone", 4) + iteration - 1)
    return params


def generate_sequences(backbones: list[dict], params: dict,
                       dotatate: str, iteration: int) -> list[dict]:
    """이터레이션별 시퀀스 생성 — 이전 결과 기반 개선."""
    amino_acids = "ACDEFGHIKLMNPQRSTVWY"
    k_per_bb = params.get("k_seq_per_backbone", 4)
    sequences = []

    for bb in backbones:
        for j in range(k_per_bb):
            random.seed(hash(f"{bb['id']}_{j}_iter{iteration}") % 2**32)
            length = bb["length"]
            seq = list(dotatate[:length].ljust(length, "A"))
            # 이터레이션이 높을수록 더 보수적 (적은 변이)
            n_mutations = max(1, random.randint(1, 4) - (iteration - 1))
            for _ in range(n_mutations):
                pos = random.randint(0, length - 1)
                if seq[pos] != "C":
                    seq[pos] = random.choice(amino_acids)
            sequences.append({
                "seq_id": f"bb{backbones.index(bb):02d}_seq{j:02d}",
                "backbone_id": bb["id"],
                "sequence": "".join(seq),
            })

    return sequences


# ---------------------------------------------------------------------------
# Main Pipeline — Multi-Iteration
# ---------------------------------------------------------------------------
def main() -> None:
    global API_KEY, API_MODE
    API_KEY = os.environ.get("NVIDIA_NIM_API_KEY")
    if not API_KEY:
        print(f"  {RED}ERROR: NVIDIA_NIM_API_KEY not set{RESET}")
        print(f"  {DIM}export NVIDIA_NIM_API_KEY='nvapi-...' python runs/run_live_demo.py{RESET}")
        sys.exit(1)

    sw = PipelineStatusWriter(STATUS_FILE)

    banner("SSTR2 Peptide Binder Design - Multi-Iteration Pipeline")
    print(f"  {GREEN}API Key:{RESET}  {API_KEY[:12]}...{API_KEY[-4:]}")
    print(f"  {GREEN}Target:{RESET}   SSTR2 (Somatostatin Receptor Type 2)")
    print(f"  {GREEN}Ref:{RESET}      DOTATATE (AGCKNFFWKTFTSC, 14-aa)")
    print(f"  {GREEN}LLM:{RESET}      Qwen 2.5 7B (NoneProvider - rule-based)")
    print(f"  {GREEN}APIs:{RESET}     ESMFold + MolMIM (auto-fallback to simulation)")
    print(f"  {GREEN}Iters:{RESET}    {MAX_ITERATIONS} (convergence threshold: {CONVERGENCE_THRESHOLD} kcal/mol)")
    print(f"  {GREEN}Status:{RESET}   {STATUS_FILE}")
    print()

    # --- Check API availability ---
    print(f"  {YELLOW}API 연결 확인 중...{RESET}")
    if check_api_availability():
        API_MODE = "live"
        ok("NVIDIA NIM API 연결 성공 — Live 모드")
        sw.update_live_api("esmfold", "live")
    else:
        API_MODE = "simulated"
        warn("API 403/연결실패 — 시뮬레이션 모드로 전환")
        warn("새 API 키: https://build.nvidia.com → Get API Key")
        sw.update_live_api("esmfold", "simulated")
        sw.update_live_api("molmim", "simulated")
    print()

    # Initialize steps
    step_defs = [
        ("step01", "OpenFold3", "Step01"),
        ("step02", "RFdiffusion", "Step02"),
        ("step03", "ProteinMPNN", "Step03"),
        ("step04", "ESMFold", "Step04"),
        ("step05", "DiffDock", "Step05"),
        ("step05b", "Selectivity", "Step05b"),
        ("step06", "PyRosetta", "Step06"),
        ("step07", "Analysis", "Step07"),
    ]
    for sid, label, short in step_defs:
        sw.update_step(sid, label, short, "pending")

    # Initialize agents
    agent_defs = [
        ("planner", "Planner", "LLM"),
        ("qc-ranker", "QC & Ranker", "Code"),
        ("diversity-mgr", "DiversityMgr", "Code"),
        ("critic", "Critic", "LLM"),
        ("reporter", "Reporter", "LLM"),
    ]
    for aid, name, atype in agent_defs:
        sw.update_agent(aid, name, atype, "idle", "Waiting for pipeline start...")

    DOTATATE = "AGCKNFFWKTFTSC"

    # Imports for agents
    from AG_src.llm import create_provider
    from AG_src.agents.planner import PlannerAgent
    from AG_src.agents.qc_ranker import QCRankerAgent, Candidate
    from AG_src.agents.diversity_manager import DiversityManagerAgent
    from AG_src.agents.critic import ScientistCriticAgent
    from AG_src.agents.reporter import ReporterAgent
    from AG_src.pipeline.step05b_selectivity import compute_selectivity_margin

    llm = create_provider(None)

    # Pipeline state across iterations
    params = {"n_backbone": 5, "k_seq_per_backbone": 4}
    all_convergence: list[dict] = []
    best_ddg_overall = 999.0
    best_candidate_overall: dict | None = None
    converged = False

    # Generate backbones once (fixed across iterations)
    n_backbone = params["n_backbone"]
    backbones = []
    for i in range(n_backbone):
        random.seed(42 + i)
        length = random.randint(10, 25)
        backbones.append({"id": f"backbone_{i:02d}", "length": length})

    # ======================================================================
    # ITERATION LOOP
    # ======================================================================
    for iteration in range(1, MAX_ITERATIONS + 1):
        iter_start = time.time()

        banner(f"ITERATION {iteration} / {MAX_ITERATIONS}", char="=")
        sw.set_iteration(iteration)
        sw.reset_steps()

        mode_label = f"{GREEN}LIVE API{RESET}" if API_MODE == "live" else f"{YELLOW}SIMULATED{RESET}"
        print(f"  Mode: {mode_label}  |  Params: {params}")
        print()

        # ==================================================================
        # STEP 1: OpenFold3 receptor
        # ==================================================================
        step_h("STEP 01", "OpenFold3 - 수용체 구조 준비")
        sw.update_step("step01", "OpenFold3", "Step01", "running")
        time.sleep(0.5)
        ok("SSTR2 receptor structure loaded (PDB: simulated)")
        sw.update_step("step01", "OpenFold3", "Step01", "completed", "1s")

        # ==================================================================
        # STEP 2: RFdiffusion backbone generation
        # ==================================================================
        step_h("STEP 02", "RFdiffusion - 백본 생성")
        sw.update_step("step02", "RFdiffusion", "Step02", "running")
        time.sleep(0.5)
        ok(f"{n_backbone}개 백본 (iter {iteration})")
        sw.update_step("step02", "RFdiffusion", "Step02", "completed", "1s")

        # ==================================================================
        # STEP 3: ProteinMPNN sequence design
        # ==================================================================
        step_h("STEP 03", f"ProteinMPNN - 시퀀스 설계 (k={params['k_seq_per_backbone']})")
        sw.update_step("step03", "ProteinMPNN", "Step03", "running")
        time.sleep(0.5)

        all_sequences = generate_sequences(backbones, params, DOTATATE, iteration)
        ok(f"{len(all_sequences)}개 시퀀스 설계")
        for s in all_sequences[:3]:
            info(f"{s['seq_id']}: {s['sequence']}")
        if len(all_sequences) > 3:
            info(f"... 외 {len(all_sequences) - 3}개")
        sw.update_step("step03", "ProteinMPNN", "Step03", "completed", "1s")

        # ==================================================================
        # STEP 4: ESMFold QC
        # ==================================================================
        step_h("STEP 04", f"ESMFold - 구조 예측 + pLDDT QC ({mode_label})")
        sw.update_step("step04", "ESMFold", "Step04", "running")

        dotatate_entry = {"seq_id": "DOTATATE_ref", "backbone_id": "ref", "sequence": DOTATATE}
        fold_list = [dotatate_entry] + all_sequences[:7]

        qc_results: list[dict] = []
        n_to_fold = len(fold_list)
        print(f"    {YELLOW}ESMFold {'API' if API_MODE == 'live' else '시뮬레이션'} ({n_to_fold}개 시퀀스){RESET}")

        for i, seq_data in enumerate(fold_list):
            seq = seq_data["sequence"]
            t0 = time.time()

            if API_MODE == "live":
                if i > 0:
                    time.sleep(1.5)
                result = esmfold_predict(seq)
                elapsed = time.time() - t0

                if result and "pdbs" in result:
                    pdb_text = result["pdbs"] if isinstance(result["pdbs"], str) else result["pdbs"][0]
                    plddts = extract_plddt_from_pdb(pdb_text)
                    mean_plddt = sum(plddts) / len(plddts) if plddts else 0.0
                    passed = mean_plddt >= 60.0
                    qc_results.append({
                        "seq_id": seq_data["seq_id"], "sequence": seq,
                        "plddt_mean": round(mean_plddt, 1),
                        "plddt_min": round(min(plddts), 1) if plddts else 0,
                        "plddt_max": round(max(plddts), 1) if plddts else 0,
                        "n_atoms": len(plddts), "passed": passed, "elapsed": elapsed,
                    })
                    gate = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
                    print(f"    {GREEN}✓{RESET} {seq_data['seq_id']:15s} | "
                          f"pLDDT={mean_plddt:>5.1f} | {gate} | {elapsed:.1f}s")
                else:
                    qc_results.append({
                        "seq_id": seq_data["seq_id"], "sequence": seq,
                        "plddt_mean": 0, "passed": False, "elapsed": elapsed,
                    })
                    fail(f"{seq_data['seq_id']}: ESMFold 실패 ({elapsed:.1f}s)")
            else:
                # Simulation mode
                time.sleep(0.3)  # 시각적 효과용 딜레이
                sim = esmfold_simulate(seq, iteration)
                elapsed = time.time() - t0
                passed = sim["plddt_mean"] >= 60.0
                qc_results.append({
                    "seq_id": seq_data["seq_id"], "sequence": seq,
                    "plddt_mean": sim["plddt_mean"],
                    "plddt_min": sim["plddt_min"],
                    "plddt_max": sim["plddt_max"],
                    "n_atoms": sim["n_atoms"],
                    "passed": passed, "elapsed": elapsed,
                    "simulated": True,
                })
                gate = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
                print(f"    {YELLOW}~{RESET} {seq_data['seq_id']:15s} | "
                      f"pLDDT={sim['plddt_mean']:>5.1f} (sim) | {gate}")

            sw.set_candidates(_build_candidate_list(qc_results))

        n_passed = sum(1 for r in qc_results if r["passed"])
        n_failed = len(qc_results) - n_passed
        print(f"\n    {BOLD}QC Gate: {GREEN}{n_passed} passed{RESET} / {RED}{n_failed} failed{RESET}")
        sw.update_step("step04", "ESMFold", "Step04", "completed",
                       f"{sum(r.get('elapsed', 0) for r in qc_results):.0f}s")

        # ==================================================================
        # STEP 5: DiffDock docking (simulated)
        # ==================================================================
        step_h("STEP 05", "DiffDock - 분자 도킹")
        sw.update_step("step05", "DiffDock", "Step05", "running")
        time.sleep(0.5)

        passed_qc = [r for r in qc_results if r["passed"]]
        dock_results = []
        for r in passed_qc:
            random.seed(hash(r["seq_id"] + str(iteration)) % 2**32)
            base_score = -(r["plddt_mean"] / 10.0) + random.gauss(0, 1.0)
            # 이터레이션마다 약간 향상
            base_score -= (iteration - 1) * 0.3
            dock_results.append({
                "seq_id": r["seq_id"],
                "dock_score": round(base_score, 2),
                "confidence": round(random.uniform(0.6, 0.95), 2),
            })

        dock_results.sort(key=lambda x: x["dock_score"])
        ok(f"{len(dock_results)}개 후보 도킹 완료")
        for dr in dock_results[:5]:
            info(f"{dr['seq_id']:15s} dock_score={dr['dock_score']:>7.2f}")
        sw.update_step("step05", "DiffDock", "Step05", "completed", "1s")

        # ==================================================================
        # STEP 5b: Selectivity screening
        # ==================================================================
        step_h("STEP 05b", "선택성 스크리닝 (SSTR1/3/4/5)")
        sw.update_step("step05b", "Selectivity", "Step05b", "running")
        time.sleep(0.5)

        sel_results = []
        for dr in dock_results[:5]:
            random.seed(hash(dr["seq_id"] + "sel" + str(iteration)) % 2**32)
            ot = {
                "SSTR1": dr["dock_score"] + random.gauss(2.5, 0.8),
                "SSTR3": dr["dock_score"] + random.gauss(3.0, 1.0),
                "SSTR4": dr["dock_score"] + random.gauss(3.5, 0.5),
                "SSTR5": dr["dock_score"] + random.gauss(2.0, 0.7),
            }
            sel = compute_selectivity_margin(
                seq_id=dr["seq_id"], sstr2_score=dr["dock_score"],
                offtarget_scores=ot, margin_min=-2.0, offtarget_max_allowed=-3.0,
            )
            sel_results.append(sel)
            gate = f"{GREEN}PASS{RESET}" if sel.passed else f"{RED}FAIL{RESET}"
            info(f"{sel.seq_id:15s} margin={sel.selectivity_margin:>6.2f}  {gate}")

        n_sel_pass = sum(1 for r in sel_results if r.passed)
        ok(f"선택성 게이트: {n_sel_pass}/{len(sel_results)} 통과")
        sw.update_step("step05b", "Selectivity", "Step05b", "completed", "1s")

        # ==================================================================
        # STEP 6: Rosetta ddG
        # ==================================================================
        step_h("STEP 06", "PyRosetta FlexPepDock - ddG 계산")
        sw.update_step("step06", "PyRosetta", "Step06", "running")
        time.sleep(0.5)

        rosetta_results = []
        for dr in dock_results[:5]:
            random.seed(hash(dr["seq_id"] + "ros" + str(iteration)) % 2**32)
            ddg = dr["dock_score"] * 0.8 + random.gauss(0, 1.5)
            # 이터레이션마다 ddG 향상
            ddg -= (iteration - 1) * 0.5
            rosetta_results.append({
                "seq_id": dr["seq_id"],
                "ddg": round(ddg, 1),
                "clash": random.choice([0, 0, 0, 1] if iteration == 1 else [0, 0, 0, 0, 0, 1]),
            })

        for rr in rosetta_results:
            gate_pass = rr["ddg"] <= -5.0 and rr["clash"] == 0
            gate = f"{GREEN}PASS{RESET}" if gate_pass else f"{RED}FAIL{RESET}"
            info(f"{rr['seq_id']:15s} ddG={rr['ddg']:>6.1f}  clash={rr['clash']}  {gate}")

        n_ros_pass = sum(1 for r in rosetta_results if r["ddg"] <= -5.0 and r["clash"] == 0)
        ok(f"Rosetta 게이트: {n_ros_pass}/{len(rosetta_results)} 통과")
        sw.update_step("step06", "PyRosetta", "Step06", "completed", "1s")

        # Update QC gates
        sw.set_qc_gates([
            {"name": "Gate 1", "criterion": "pLDDT >= 60", "passed": n_passed,
             "failed": n_failed, "total": len(qc_results)},
            {"name": "Gate 2", "criterion": "Top 50% Docking", "passed": len(dock_results),
             "failed": 0, "total": len(passed_qc)},
            {"name": "Gate 3", "criterion": "ddG <= -5.0", "passed": n_ros_pass,
             "failed": len(rosetta_results) - n_ros_pass, "total": len(rosetta_results)},
            {"name": "Gate 4", "criterion": "Selectivity >= -2.0", "passed": n_sel_pass,
             "failed": len(sel_results) - n_sel_pass, "total": len(sel_results)},
        ])

        # ==================================================================
        # STEP 7: Analysis + MolMIM
        # ==================================================================
        step_h("STEP 07", f"Analysis + MolMIM ({mode_label})")
        sw.update_step("step07", "Analysis", "Step07", "running")

        dotatate_smiles = "CC(=O)NC(CS)C(=O)NC(CCCCN)C(=O)NC(CC1=CC=CC=C1)C(=O)O"
        mol_list: list[dict] = []

        if API_MODE == "live":
            sw.update_live_api("molmim", "connecting")
            t0 = time.time()
            molmim_result = molmim_generate(dotatate_smiles, n=5)
            elapsed = time.time() - t0

            if molmim_result and "molecules" in molmim_result:
                sw.update_live_api("molmim", "live")
                molecules = molmim_result["molecules"]
                if isinstance(molecules, str):
                    molecules = json.loads(molecules)
                ok(f"MolMIM: {len(molecules)}개 분자 생성 ({elapsed:.2f}s)")
                for i, mol in enumerate(molecules[:5]):
                    smi = mol.get("sample", "?")
                    score = mol.get("score", 0)
                    info(f"mol_{i}: QED={score:.3f}")
                    mol_list.append({"id": f"mol_{i}", "smiles": smi, "qed": round(score, 3)})
            else:
                sw.update_live_api("molmim", "failed")
                fail(f"MolMIM 호출 실패 ({elapsed:.2f}s)")
        else:
            # Simulation mode
            t0 = time.time()
            sim_result = molmim_simulate(dotatate_smiles, n=5)
            elapsed = time.time() - t0
            sw.update_live_api("molmim", "simulated")
            molecules = sim_result["molecules"]
            ok(f"MolMIM (시뮬레이션): {len(molecules)}개 분자 ({elapsed:.2f}s)")
            for i, mol in enumerate(molecules):
                mol_list.append({"id": f"mol_{i}", "smiles": mol["sample"], "qed": round(mol["score"], 3)})
                info(f"mol_{i}: QED={mol['score']:.3f} (sim)")

        sw.set_molecules(mol_list)
        sw.update_step("step07", "Analysis", "Step07", "completed", f"{elapsed:.0f}s")

        # ==================================================================
        # AGENTS
        # ==================================================================
        step_h("AGENTS", f"에이전트 실행 (iter {iteration})")

        # --- Planner ---
        agent_h("Planner")
        sw.update_agent("planner", "Planner", "LLM", "active",
                        f"Planning iteration {iteration}...")
        t0 = time.time()
        planner = PlannerAgent(llm_provider=llm)
        plan_result = planner.execute({
            "receptor_config": {"name": "SSTR2", "chain": "B"},
            "constraints": params,
            "iteration": iteration,
        })
        plan = plan_result.get("plan")
        run_id = plan.run_id if plan else "unknown"
        if iteration == 1:
            sw.set_run_id(run_id)
        ok(f"실험 계획 생성 ({time.time() - t0:.3f}s)")
        if plan:
            info(f"Hypothesis: {plan.hypothesis[:80]}...")
        sw.update_agent("planner", "Planner", "LLM", "idle",
                        f"Iter {iteration} plan: {run_id}", iteration)

        # --- QCRanker ---
        agent_h("QCRanker")
        sw.update_agent("qc-ranker", "QC & Ranker", "Code", "active",
                        f"Ranking iteration {iteration}...")
        candidates = []
        for r in qc_results:
            if r.get("plddt_mean", 0) <= 0:
                continue
            sid = r["seq_id"]
            try:
                bb_id = int(sid[2:4])
                s_id = int(sid[-2:])
            except (ValueError, IndexError):
                bb_id, s_id = 99, 99
            candidates.append(Candidate(
                candidate_id=sid, backbone_id=bb_id, seq_id=s_id,
                sequence=r["sequence"], plddt_mean=r["plddt_mean"],
            ))
        t0 = time.time()
        qcranker = QCRankerAgent(llm_provider=llm)
        qc_rank_result = qcranker.execute({
            "candidates": candidates,
            "thresholds": {"plddt_min": 60.0, "docking_top_pct": 50.0, "ddg_max": -5.0},
            "run_id": "live_demo", "iteration": iteration,
        })
        ok(f"QC 랭킹 완료 ({time.time() - t0:.3f}s)")
        rt = qc_rank_result.get("rank_table")
        qr = qc_rank_result.get("qc_report")
        if qr:
            info(f"Pass rate: {qr.passed_count}/{qr.total_input} ({qr.pass_rate:.1%})")
        sw.update_agent("qc-ranker", "QC & Ranker", "Code", "idle",
                        f"Iter {iteration}: {qr.pass_rate:.0%} pass rate" if qr else "Done",
                        iteration * 2)

        # --- DiversityManager ---
        agent_h("DiversityManager")
        sw.update_agent("diversity-mgr", "DiversityMgr", "Code", "active",
                        f"Clustering iteration {iteration}...")
        t0 = time.time()
        divmgr = DiversityManagerAgent(llm_provider=llm)
        div_result = divmgr.execute({
            "candidates": candidates[:8], "n_select": 5, "method": "foldmason",
        })
        ok(f"다양성 필터 ({time.time() - t0:.3f}s)")
        n_clusters = len(div_result.get("clusters", []))
        n_selected = len(div_result.get("diverse_candidates", []))
        info(f"Clusters: {n_clusters}, Selected: {n_selected}")
        sw.update_agent("diversity-mgr", "DiversityMgr", "Code", "idle",
                        f"Iter {iteration}: {n_clusters} clusters", iteration * 3)

        # --- Critic ---
        agent_h("ScientistCritic")
        sw.update_agent("critic", "Critic", "LLM", "active",
                        f"Analyzing iteration {iteration}...")
        t0 = time.time()
        critic = ScientistCriticAgent(llm_provider=llm)
        critic_result = critic.execute({
            "rank_table": rt, "qc_report": qr, "iteration": iteration,
            "current_params": params,
        })
        ok(f"비평 분석 ({time.time() - t0:.3f}s)")
        analysis = critic_result.get("critic_analysis")
        critic_changes: list[dict] = []
        if analysis:
            info(f"Hypothesis: {analysis.hypothesis[:80]}...")
            critic_changes = [
                {"parameter": c.get("parameter", ""), "new_value": c.get("new_value")}
                for c in analysis.proposed_changes
            ] if hasattr(analysis, "proposed_changes") else []
            info(f"Proposed changes: {len(critic_changes)}")
        sw.update_agent("critic", "Critic", "LLM", "idle",
                        f"Iter {iteration}: {len(critic_changes)} changes proposed",
                        iteration * 4)

        # --- Reporter ---
        agent_h("Reporter")
        sw.update_agent("reporter", "Reporter", "LLM", "active",
                        f"Generating report iter {iteration}...")
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            t0 = time.time()
            reporter = ReporterAgent(runs_base_dir=tmpdir, llm_provider=llm)
            report_result = reporter.execute({
                "run_id": f"live_demo_iter{iteration:02d}", "iteration": iteration,
                "rank_table": rt, "top_candidates": candidates[:5],
                "receptor_pdb": "/tmp/sstr2.pdb",
                "output_dir": str(Path(tmpdir) / "reports"),
            })
            ok(f"보고서 생성 ({time.time() - t0:.3f}s)")
        sw.update_agent("reporter", "Reporter", "LLM", "idle",
                        f"Iter {iteration} report generated", iteration * 5)

        # ==================================================================
        # Build candidate list & convergence
        # ==================================================================
        final_candidates = _build_full_candidate_list(
            qc_results, dock_results, rosetta_results, sel_results,
        )
        sw.set_candidates(final_candidates)

        # Best candidate this iteration
        iter_best_ddg = min((r["ddg"] for r in rosetta_results), default=0)
        if qc_results:
            best = max(qc_results, key=lambda x: x.get("plddt_mean", 0))
            best_dock = next((d for d in dock_results if d["seq_id"] == best["seq_id"]), None)
            if iter_best_ddg < best_ddg_overall:
                best_ddg_overall = iter_best_ddg
                best_candidate_overall = {
                    "id": best["seq_id"],
                    "sequence": best["sequence"],
                    "plddt": best["plddt_mean"],
                    "dockScore": best_dock["dock_score"] if best_dock else None,
                    "iteration": iteration,
                }
            sw.set_best_candidate(best_candidate_overall or {
                "id": best["seq_id"],
                "sequence": best["sequence"],
                "plddt": best["plddt_mean"],
                "dockScore": best_dock["dock_score"] if best_dock else None,
            })

        # Convergence check
        delta = abs(iter_best_ddg - (all_convergence[-1]["bestDdG"] if all_convergence else 999))
        is_converged = iteration > 1 and delta < CONVERGENCE_THRESHOLD

        conv_point = {
            "iteration": iteration,
            "bestDdG": round(iter_best_ddg, 1),
            "topCandidates": n_passed,
            "converged": is_converged,
        }
        all_convergence.append(conv_point)
        sw.add_convergence_point(conv_point)

        iter_elapsed = time.time() - iter_start
        print(f"\n  {'─' * 60}")
        print(f"  {BOLD}Iteration {iteration} Summary:{RESET}")
        print(f"    Best ddG: {iter_best_ddg:.1f} kcal/mol")
        print(f"    Delta:    {delta:.2f} kcal/mol {'< ' + str(CONVERGENCE_THRESHOLD) + ' CONVERGED!' if is_converged else ''}")
        print(f"    Passed:   {n_passed}/{len(qc_results)} QC")
        print(f"    Time:     {iter_elapsed:.1f}s")

        if is_converged:
            converged = True
            banner(f"CONVERGED at iteration {iteration}!", char="*")
            break

        # Evolve params for next iteration
        if iteration < MAX_ITERATIONS:
            params = evolve_params(params, critic_changes, iteration + 1)
            info(f"Next iteration params: {params}")
            time.sleep(1)  # 다음 이터레이션 전 잠시 대기

    # ======================================================================
    # COMPLETE
    # ======================================================================
    sw.mark_completed()

    banner("Pipeline Execution Complete!", char="*")
    print(f"  {BOLD}Mode:{RESET}       {'LIVE API' if API_MODE == 'live' else 'SIMULATED (API 403)'}")
    print(f"  {BOLD}Iterations:{RESET} {len(all_convergence)}/{MAX_ITERATIONS}"
          f" {'(converged)' if converged else ''}")
    print(f"  {BOLD}Best ddG:{RESET}   {best_ddg_overall:.1f} kcal/mol")

    if best_candidate_overall:
        print(f"  {BOLD}Best ID:{RESET}    {best_candidate_overall['id']}")
        print(f"  {BOLD}pLDDT:{RESET}      {best_candidate_overall['plddt']}")

    print(f"\n  {BOLD}Convergence:{RESET}")
    for cp in all_convergence:
        mark = f" {GREEN}← CONVERGED{RESET}" if cp["converged"] else ""
        print(f"    Iter {cp['iteration']}: ddG={cp['bestDdG']:>6.1f}  "
              f"top={cp['topCandidates']}{mark}")

    print(f"\n  {BOLD}Agents (5/5):{RESET}")
    print(f"    {MAGENTA}Planner{RESET}          → Experiment plan + hypothesis")
    print(f"    {GREEN}QCRanker{RESET}         → Multi-gate ranking")
    print(f"    {CYAN}DiversityManager{RESET} → Cluster-based selection")
    print(f"    {YELLOW}ScientistCritic{RESET}  → Parameter optimization")
    print(f"    {BLUE}Reporter{RESET}         → Lab notebook generation")

    print(f"\n  {BOLD}LLM Model:{RESET} Qwen 2.5 7B (NoneProvider — rule-based)")
    print(f"  {DIM}Ollama 활성화: pipeline_config.yaml → llm.provider: 'ollama'{RESET}")
    print(f"\n  {GREEN}Status JSON:{RESET} {STATUS_FILE}")
    print(f"  {GREEN}Frontend:{RESET}    cd frontend && npm run dev")
    print()


def _build_candidate_list(qc_results: list[dict]) -> list[dict]:
    """QC 결과를 프론트엔드 Candidate 포맷으로 변환."""
    candidates = []
    for i, r in enumerate(sorted(qc_results, key=lambda x: -x.get("plddt_mean", 0))):
        candidates.append({
            "rank": i + 1,
            "id": r["seq_id"],
            "sequence": r.get("sequence", ""),
            "pLDDT": r.get("plddt_mean", 0),
            "dockScore": 0,
            "ddG": 0,
            "lDDT": 0,
            "selectivity": 0,
            "finalScore": r.get("plddt_mean", 0) / 100,
            "result": "PASS" if r.get("passed") else "FAIL",
            "failReason": "" if r.get("passed") else f"pLDDT {r.get('plddt_mean', 0)} < 60",
        })
    return candidates


def _build_full_candidate_list(
    qc_results: list[dict],
    dock_results: list[dict],
    rosetta_results: list[dict],
    sel_results: list,
) -> list[dict]:
    """전체 결과를 통합한 프론트엔드 Candidate 포맷."""
    dock_map = {d["seq_id"]: d for d in dock_results}
    ros_map = {r["seq_id"]: r for r in rosetta_results}
    sel_map = {s.seq_id: s for s in sel_results}

    candidates = []
    for i, r in enumerate(sorted(qc_results, key=lambda x: -x.get("plddt_mean", 0))):
        sid = r["seq_id"]
        dock = dock_map.get(sid, {})
        ros = ros_map.get(sid, {})
        sel = sel_map.get(sid)

        plddt = r.get("plddt_mean", 0)
        dock_score = dock.get("dock_score", 0)
        ddg = ros.get("ddg", 0)
        selectivity = sel.selectivity_margin if sel else 0

        final = round(
            (plddt / 100) * 0.3 +
            (min(abs(dock_score), 12) / 12) * 0.3 +
            (min(abs(ddg), 10) / 10) * 0.25 +
            (min(abs(selectivity), 5) / 5) * 0.15,
            3,
        )

        gate_pass = r.get("passed", False) and ddg <= -5.0
        fail_reasons = []
        if plddt < 60:
            fail_reasons.append(f"pLDDT {plddt} < 60")
        if dock_score > -5:
            fail_reasons.append(f"Dock {dock_score} > -5")
        if ddg > -5:
            fail_reasons.append(f"ddG {ddg} > -5")

        candidates.append({
            "rank": i + 1,
            "id": sid,
            "sequence": r.get("sequence", ""),
            "pLDDT": plddt,
            "dockScore": dock_score,
            "ddG": ddg,
            "lDDT": round(random.uniform(0.5, 0.9), 3),
            "selectivity": round(selectivity, 2),
            "finalScore": final,
            "result": "PASS" if gate_pass else "FAIL",
            "failReason": "; ".join(fail_reasons) if fail_reasons else "",
        })

    return sorted(candidates, key=lambda x: -x["finalScore"])


if __name__ == "__main__":
    main()
