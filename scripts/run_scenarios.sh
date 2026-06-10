#!/bin/bash
set -euo pipefail
# Run all 3 MolMIM scenarios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true

cd "$REPO_ROOT/bionemo"

echo "============================================"
echo "  Running Scenario 1: Generation & Comparison"
echo "============================================"
python 01_embedding_similarity.py 2>&1

echo ""
echo "============================================"
echo "  Running Scenario 2: Molecule Generation"
echo "============================================"
python 02_molecule_generation.py --num-molecules 5 2>&1

echo ""
echo "============================================"
echo "  Running Scenario 3: Multi-round Optimization"
echo "============================================"
python 03_property_optimization.py --rounds 2 --num-molecules 5 2>&1
