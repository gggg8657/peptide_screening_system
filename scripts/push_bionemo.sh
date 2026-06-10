#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true

cd "$REPO_ROOT"

echo "=== Pull latest from prst/main ==="
git pull prst main --rebase 2>&1

echo ""
echo "=== Add bionemo/ and updated files ==="
git add .gitignore
git add bionemo/__init__.py
git add bionemo/.env.example
git add bionemo/requirements.txt
git add bionemo/README.md
git add bionemo/molmim_client.py
git add bionemo/01_embedding_similarity.py
git add bionemo/02_molecule_generation.py
git add bionemo/03_property_optimization.py
git add scripts/run_scenarios.sh
git add scripts/test_molmim.sh
git add scripts/test_molmim_curl.sh

echo ""
echo "=== Staged files ==="
git diff --cached --stat

echo ""
echo "=== Commit ==="
git commit -m "feat: add BioNeMo MolMIM API client and scenarios

- MolMIM client (molmim_client.py) for NVIDIA hosted API
- 3 scenario scripts: embedding comparison, molecule generation, property optimization
- Auto key loading from molmim.key / .env / env vars
- README with usage docs, endpoint reference, model info
- .gitignore updated to exclude API keys and secrets"

echo ""
echo "=== Push to prst remote ==="
git push prst main 2>&1

echo ""
echo "=== Done ==="
git log --oneline -3
