#!/usr/bin/env bash
# ============================================================
# Full Experiment Pipeline — Phase 1 → 2A → 2B
#
# Runs all 54 experiments with automatic model swaps.
# Phase 2A/2B matrices must be pre-populated after Phase 1/2A.
#
# Usage:
#   bash llm_benchmark/run_all.sh           # full run
#   bash llm_benchmark/run_all.sh --dry-run # plan only
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$SCRIPT_DIR/outputs"
mkdir -p "$LOG_DIR"

echo "╔══════════════════════════════════════════════╗"
echo "║  LLM Benchmark — Full Pipeline               ║"
echo "║  54 experiments across 3 phases               ║"
echo "║  Estimated: ~12 hours (parallelized)          ║"
echo "║  Started: $(date '+%Y-%m-%d %H:%M')                       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

ARGS="${*:-}"

# Phase 1
echo "━━━ Phase 1: Model Screening (15 runs) ━━━"
bash "$SCRIPT_DIR/run_phase1.sh" $ARGS 2>&1 | tee "$LOG_DIR/phase1_${TIMESTAMP}.log"
echo ""

if [[ "$ARGS" == *"--dry-run"* ]]; then
    echo "━━━ Phase 2A: [DRY RUN — skipped, needs Phase 1 results] ━━━"
    echo "━━━ Phase 2B: [DRY RUN — skipped, needs Phase 2A results] ━━━"
    exit 0
fi

# Phase 1 → 2A: auto-populate top models
echo "━━━ Analyzing Phase 1 results... ━━━"
python3 -c "
import json, yaml
from pathlib import Path

outputs = Path('$SCRIPT_DIR/outputs/phase1')
summary = outputs / '_phase_summary.json'
if not summary.exists():
    print('ERROR: Phase 1 summary not found'); exit(1)

# Aggregate SES by model (placeholder — real logic in scoring/aggregate.py)
results = json.loads(summary.read_text())
done = [r for r in results if r['status'] == 'done']
print(f'Phase 1: {len(done)} completed experiments')

# TODO: Real SES aggregation here
# For now, just list unique models that completed
models = sorted(set(r['id'].split('-')[0] + '-' + r['id'].split('-')[1] for r in done))
print(f'Models with results: {len(models)}')
print('Phase 2A matrix must be manually populated after SES analysis.')
"
echo ""

# Phase 2A
echo "━━━ Phase 2A: Flow Pattern Comparison (27 runs) ━━━"
bash "$SCRIPT_DIR/run_phase2a.sh" $ARGS 2>&1 | tee "$LOG_DIR/phase2a_${TIMESTAMP}.log"
echo ""

# Phase 2B
echo "━━━ Phase 2B: Sub-variable Exploration (12 runs) ━━━"
bash "$SCRIPT_DIR/run_phase2b.sh" $ARGS 2>&1 | tee "$LOG_DIR/phase2b_${TIMESTAMP}.log"
echo ""

echo "╔══════════════════════════════════════════════╗"
echo "║  ALL PHASES COMPLETE                          ║"
echo "║  Finished: $(date '+%Y-%m-%d %H:%M')                      ║"
echo "╚══════════════════════════════════════════════╝"
