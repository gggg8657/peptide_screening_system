#!/usr/bin/env bash
# ============================================================
# Phase 2B Retry + Phase 3 — 연속 실행
#
# Phase 2B retry: 12 experiments (debate rounds + cross-model)
# Phase 3:        44 experiments (scaling + statistical power)
# Total:          56 experiments
# Estimated:      ~5hr
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

echo "╔══════════════════════════════════════════════╗"
echo "║  Phase 2B Retry + Phase 3                    ║"
echo "║  56 experiments, ~5hr                         ║"
echo "║  Started: $(date '+%Y-%m-%d %H:%M')                       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─── Phase 2B Retry ───
echo "━━━ Phase 2B Retry (12 experiments) ━━━"
bash "$SCRIPT_DIR/run_phase2b_retry.sh" 2>&1 | tee "$LOG_DIR/phase2b_retry_${TIMESTAMP}.log"
echo ""

# ─── Phase 3 ───
echo "━━━ Phase 3 (44 experiments) ━━━"
echo ""

# GPU 좀비 정리
pkill -9 -f "VLLM::EngineCore" 2>/dev/null || true
sleep 3

python -m llm_benchmark.harness.parallel_launcher phase3 --max-parallel 3 2>&1 | tee "$LOG_DIR/phase3_${TIMESTAMP}.log"
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

for phase in ["phase2b", "phase3"]:
    phase_dir = Path(f"llm_benchmark/outputs/{phase}")
    if not phase_dir.exists(): continue
    for run_dir in sorted(phase_dir.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("_"): continue
        if (run_dir / "ses_score.json").exists(): continue
        sf = run_dir / "status.json"
        if not sf.exists(): continue
        st = json.loads(sf.read_text())
        if st.get("state") != "done": continue
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

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ALL COMPLETE                                 ║"
echo "║  Finished: $(date '+%Y-%m-%d %H:%M')                      ║"
echo "╚══════════════════════════════════════════════╝"
