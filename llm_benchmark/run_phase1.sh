#!/usr/bin/env bash
# ============================================================
# Phase 1: Model Screening (5 models × Sequential × 3 seeds)
#
# Strategy:
#   - 5 model groups, sequential model swaps
#   - 3 experiments per group, parallel
#   - Estimated: ~1.5 hours
#
# Usage:
#   bash llm_benchmark/run_phase1.sh
#   bash llm_benchmark/run_phase1.sh --dry-run
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "╔══════════════════════════════════════════════╗"
echo "║  Phase 1: Model Screening                    ║"
echo "║  5 models × 3 seeds = 15 experiments         ║"
echo "║  Max parallel per model: 3                   ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

source ~/miniforge3/etc/profile.d/conda.sh
conda activate bio-tools

export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri:${PYTHONPATH:-}"
export CUDA_VISIBLE_DEVICES=2,3

python -m llm_benchmark.harness.parallel_launcher phase1 --max-parallel 3 "$@"

echo ""
echo "Phase 1 complete. Results: llm_benchmark/outputs/phase1/"
echo "Run analysis: python -m llm_benchmark.scoring.aggregate phase1"
