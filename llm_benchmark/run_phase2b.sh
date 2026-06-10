#!/usr/bin/env bash
# ============================================================
# Phase 2B: Sub-variable Exploration (ablation study)
#
# Strategy:
#   - Single best model (no model swap needed)
#   - 12 experiments: 4 configs × 3 seeds
#   - Batch 3 parallel at a time
#   - Estimated: ~3.3 hours
#
# Prerequisites:
#   - Phase 2A complete, best_model filled in phase2b_matrix.yaml
#
# Usage:
#   bash llm_benchmark/run_phase2b.sh
#   bash llm_benchmark/run_phase2b.sh --dry-run
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "╔══════════════════════════════════════════════╗"
echo "║  Phase 2B: Sub-variable Exploration          ║"
echo "║  Best model × 4 configs × 3 seeds = 12 exp  ║"
echo "║  Max parallel: 3                             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

source ~/miniforge3/etc/profile.d/conda.sh
conda activate bio-tools

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri:${PYTHONPATH:-}"
export CUDA_VISIBLE_DEVICES=2,3

python -m llm_benchmark.harness.parallel_launcher phase2b --max-parallel 3 "$@"

echo ""
echo "Phase 2B complete. Results: llm_benchmark/outputs/phase2b/"
