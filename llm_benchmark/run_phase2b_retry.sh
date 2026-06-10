#!/usr/bin/env bash
# ============================================================
# Phase 2B Retry — cross-model + debate rounds 구분 실험
#
# 기존 Phase 2B에서 디렉토리명 충돌로 누락된 실험을 재실행.
# - collaborative: rounds=2 vs rounds=3 구분
# - hierarchical: same vs cross(DeepSeek) 구분
# - cross-model: GPU2=DeepSeek + GPU3=Qwen3 동시 서빙
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

source ~/miniforge3/etc/profile.d/conda.sh
conda activate bio-tools

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri:${PYTHONPATH:-}"
export CUDA_VISIBLE_DEVICES=2,3

echo "╔══════════════════════════════════════════════╗"
echo "║  Phase 2B Retry — 12 experiments             ║"
echo "║  GPU2: DeepSeek-R1 (cross-model orchestrator)║"
echo "║  GPU3: Qwen3-32B (main model)                ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

python3 << 'PYEOF'
import json, os, sys, time, subprocess, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("phase2b_retry")

REPO = Path(os.environ.get("REPO_ROOT", ".")).resolve()
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"))

from llm_benchmark.harness.model_swap import start_model, stop_slot, _kill_slot
from llm_benchmark.runners.base import ExperimentConfig
from llm_benchmark.runners import get_runner
from concurrent.futures import ProcessPoolExecutor, as_completed

OUTPUT_BASE = REPO / "llm_benchmark" / "outputs" / "phase2b"

# ── Define 12 experiments with unique dir names ──
experiments = []
seeds = [42, 137, 256]

# Collaborative: rounds=2
for s in seeds:
    experiments.append({
        "id": f"P2B-R2-s{s}", "model": "qwen3_32b", "flow": "collaborative",
        "seed": s, "gate_mode": "adaptive", "debate_max_rounds": 2,
        "dir_suffix": "rounds2", "vllm_port": 8002,  # GPU3 only
    })
# Collaborative: rounds=3
for s in seeds:
    experiments.append({
        "id": f"P2B-R3-s{s}", "model": "qwen3_32b", "flow": "collaborative",
        "seed": s, "gate_mode": "adaptive", "debate_max_rounds": 3,
        "dir_suffix": "rounds3", "vllm_port": 8002,
    })
# Hierarchical: same model
for s in seeds:
    experiments.append({
        "id": f"P2B-HS-s{s}", "model": "qwen3_32b", "flow": "hierarchical",
        "seed": s, "gate_mode": "adaptive", "orchestrator_model": "same",
        "dir_suffix": "orch_same", "vllm_port": 8002,
    })
# Hierarchical: cross model (Orchestrator=DeepSeek on GPU2:8003)
for s in seeds:
    experiments.append({
        "id": f"P2B-HC-s{s}", "model": "qwen3_32b", "flow": "hierarchical",
        "seed": s, "gate_mode": "adaptive", "orchestrator_model": "cross",
        "orchestrator_cross_model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "dir_suffix": "orch_cross", "vllm_port": 8002,
    })

# ── Load models: GPU2=DeepSeek, GPU3=Qwen3 ──
log.info("Loading GPU2: DeepSeek-R1-32B (for cross-model orchestrator)")
ok0 = start_model(0, "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
if not ok0:
    log.warning("GPU2 DeepSeek load failed — cross-model experiments will use fallback")

log.info("Loading GPU3: Qwen3-32B")
ok1 = start_model(1, "Qwen/Qwen3-32B")
if not ok1:
    log.error("GPU3 Qwen3-32B load failed — aborting")
    sys.exit(1)

# ── Run function ──
def run_one(exp):
    exp_id = exp["id"]
    model_id = exp["model"]
    flow = exp["flow"]
    seed = exp["seed"]
    suffix = exp["dir_suffix"]

    output_dir = str(OUTPUT_BASE / f"{model_id}__{flow}__adaptive__{suffix}__s{seed}")

    # Skip if done
    status_f = Path(output_dir) / "status.json"
    if status_f.exists():
        try:
            st = json.loads(status_f.read_text())
            if st.get("state") == "done":
                return {"id": exp_id, "status": "skipped"}
        except: pass

    from llm_benchmark.runners.base import ExperimentConfig
    from llm_benchmark.runners import get_runner

    config = ExperimentConfig(
        experiment_id=exp_id, model_id=model_id,
        model_hf_id="Qwen/Qwen3-32B", flow=flow, seed=seed,
        n_candidates=8, max_iterations=5, top_k=5,
        output_dir=output_dir,
        extra={k: v for k, v in exp.items()
               if k not in ("id","model","flow","seed","dir_suffix","vllm_port")
              } | {"vllm_port": exp["vllm_port"]},
    )

    runner_cls = get_runner(flow)
    runner = runner_cls(config)
    result = runner.run()
    return {"id": exp_id, "status": "done" if result.get("success") else "failed", "elapsed": result.get("elapsed_s",0)}

# ── Run in batches of 3 ──
log.info("Running %d experiments (3 parallel)", len(experiments))
results = []
with ProcessPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(run_one, e): e for e in experiments}
    for f in as_completed(futures):
        r = f.result()
        log.info("  %s: %s", r["id"], r["status"])
        results.append(r)

done = sum(1 for r in results if r["status"] == "done")
skip = sum(1 for r in results if r["status"] == "skipped")
fail = sum(1 for r in results if r["status"] == "failed")
log.info("COMPLETE: done=%d skipped=%d failed=%d", done, skip, fail)

# Save summary
(OUTPUT_BASE / "_phase2b_retry_summary.json").write_text(json.dumps(results, indent=2))
PYEOF

echo ""
echo "Phase 2B retry complete. Results: llm_benchmark/outputs/phase2b/"
