#!/usr/bin/env bash
# ============================================================
# V2 Pipeline — Full Experiment Suite
#
# V2 Phase 1: V1 vs V2 직접 비교 (18 experiments)
# V2 Phase 2: V2 flow 패턴 비교 (18 experiments, Phase 1 후)
# Total: 36 experiments
# Estimated: ~3hr (2-GPU parallel)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$SCRIPT_DIR/outputs"

cd "$REPO_ROOT"

source ~/miniforge3/etc/profile.d/conda.sh
conda activate bio-tools

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri:${PYTHONPATH:-}"
export CUDA_VISIBLE_DEVICES=2,3

# GPU 좀비 정리
pkill -9 -f "VLLM::EngineCore" 2>/dev/null || true
sleep 3

echo "╔══════════════════════════════════════════════╗"
echo "║  V2 Pipeline — LLM-Direct Mutation           ║"
echo "║  36 experiments, ~3hr                         ║"
echo "║  Started: $(date '+%Y-%m-%d %H:%M')                       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─── V2 Phase 1: V1 vs V2 비교 ───
echo "━━━ V2 Phase 1: V1 vs V2 Direct Comparison (18 runs) ━━━"
mkdir -p "$SCRIPT_DIR/outputs/v2_phase1"
python -m llm_benchmark.harness.parallel_launcher v2_phase1 --max-parallel 3 "$@" 2>&1 | tee "$LOG_DIR/v2_phase1_${TIMESTAMP}.log"
echo ""

# ─── SES 계산 ───
echo "━━━ SES Computation ━━━"
python3 << 'PYEOF'
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
sys.path.insert(0, "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri")
from llm_benchmark.scoring.ses import CandidateScore, compute_ses, is_hit

FWKT_REF = {7: "F", 8: "W", 9: "K", 10: "T"}
count = 0
for phase in ["v2_phase1"]:
    phase_dir = Path(f"llm_benchmark/outputs/{phase}")
    if not phase_dir.exists(): continue
    for run_dir in sorted(phase_dir.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("_"): continue
        if (run_dir / "ses_score.json").exists(): continue
        sf = run_dir / "status.json"
        if not sf.exists(): continue
        if json.loads(sf.read_text()).get("state") != "done": continue
        flow_dir = run_dir / "pyrosetta_flow" / "sst14_agentic_mutdock"
        candidates = []; first_hit_iter = 0
        for iter_dir in sorted(flow_dir.glob("iter_*")):
            mf = iter_dir / "08_reports" / "iteration_manifest.json"
            if not mf.exists(): continue
            iter_num = int(iter_dir.name.split("_")[1])
            for c in json.loads(mf.read_text()).get("candidates", []):
                seq = c.get("sequence", ""); ddg = c.get("ddg", 999.0)
                clash = c.get("clash_count", 0) or 0
                fwkt_ok = all(seq[p-1] == e for p, e in FWKT_REF.items()) if len(seq) >= 14 else False
                cs = CandidateScore(candidate_id=c.get("candidate_id",""), sequence=seq,
                    ddg=ddg, clash_score=float(clash), fwkt_conserved=fwkt_ok, cluster_id=c.get("cluster_id"))
                candidates.append(cs)
                if first_hit_iter == 0 and is_hit(cs): first_hit_iter = iter_num
        if not candidates: continue
        max_iter = max(int(d.name.split("_")[1]) for d in flow_dir.glob("iter_*") if d.is_dir())
        ses = compute_ses(candidates=candidates, first_hit_iter=first_hit_iter, max_iterations=max_iter)
        (run_dir / "ses_score.json").write_text(json.dumps(ses, indent=2), encoding="utf-8")
        count += 1
print(f"SES computed for {count} experiments")
PYEOF

# ─── V1 vs V2 비교 결과 ───
echo ""
echo "━━━ V1 vs V2 Comparison ━━━"
python3 << 'PYEOF'
import json, statistics
from pathlib import Path
from collections import defaultdict

data = defaultdict(list)

# V1 results (from phase2a sequential)
p2a = Path("llm_benchmark/outputs/phase2a")
if p2a.exists():
    for run_dir in sorted(p2a.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("_"): continue
        if "sequential" not in run_dir.name: continue
        ses_f = run_dir / "ses_score.json"
        if not ses_f.exists(): continue
        ses = json.loads(ses_f.read_text())
        model = run_dir.name.split("__")[0]
        data[f"{model}__V1"].append(ses["ses"])

# V2 results
v2p1 = Path("llm_benchmark/outputs/v2_phase1")
if v2p1.exists():
    for run_dir in sorted(v2p1.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("_"): continue
        ses_f = run_dir / "ses_score.json"
        if not ses_f.exists(): continue
        ses = json.loads(ses_f.read_text())
        model = run_dir.name.split("__")[0]
        data[f"{model}__V2"].append(ses["ses"])

print(f"{'Model__Version':<35} {'SES Mean':>10} {'SES Std':>10} {'N':>5}")
print("─" * 65)
for key in sorted(data):
    vals = data[key]
    mean = statistics.mean(vals) if vals else 0
    std = statistics.stdev(vals) if len(vals) >= 2 else 0
    print(f"{key:<35} {mean:>10.4f} {std:>10.4f} {len(vals):>5}")
PYEOF

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  V2 Phase 1 COMPLETE                          ║"
echo "║  Finished: $(date '+%Y-%m-%d %H:%M')                      ║"
echo "╚══════════════════════════════════════════════╝"
