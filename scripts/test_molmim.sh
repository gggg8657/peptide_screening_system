#!/bin/bash
# Activate conda
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true

echo "Python: $(which python)"
echo ""

cd "$REPO_ROOT/bionemo"
pip install requests python-dotenv -q 2>&1 | tail -3
echo "--- Running molmim_client.py ---"
python molmim_client.py 2>&1
