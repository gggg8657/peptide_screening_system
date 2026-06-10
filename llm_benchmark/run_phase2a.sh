#!/usr/bin/env bash
# ============================================================
# Phase 2A: Flow Pattern Comparison (Top-3 × 3 flows × 3 seeds)
#
# Strategy:
#   - 3 model groups, sequential model swaps
#   - 9 experiments per group (3 flows × 3 seeds)
#   - Batch 3 parallel at a time (same flow, 3 seeds)
#   - Estimated: ~7.5 hours
#
# Prerequisites:
#   - Phase 1 complete, top_models filled in phase2a_matrix.yaml
#
# Usage:
#   bash llm_benchmark/run_phase2a.sh
#   bash llm_benchmark/run_phase2a.sh --dry-run
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Check phase2a_matrix has experiments
MATRIX="$SCRIPT_DIR/configs/phase2a_matrix.yaml"
EXP_COUNT=$(python3 -c "import yaml; d=yaml.safe_load(open('$MATRIX')); print(len(d.get('experiments',[])))")
if [ "$EXP_COUNT" -eq 0 ]; then
    echo "ERROR: phase2a_matrix.yaml has no experiments."
    echo "Run Phase 1 analysis first to populate top_models and experiments."
    exit 1
fi

echo "╔══════════════════════════════════════════════╗"
echo "║  Phase 2A: Flow Pattern Deep Comparison      ║"
echo "║  Top-3 models × 3 flows × 3 seeds = 27 exp  ║"
echo "║  Max parallel per model: 6                   ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

source ~/miniforge3/etc/profile.d/conda.sh
conda activate bio-tools

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri:${PYTHONPATH:-}"
export CUDA_VISIBLE_DEVICES=2,3

python -m llm_benchmark.harness.parallel_launcher phase2a --max-parallel 6 "$@"

echo ""
echo "Phase 2A complete. Results: llm_benchmark/outputs/phase2a/"
