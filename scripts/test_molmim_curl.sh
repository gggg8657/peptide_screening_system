#!/bin/bash
# Test MolMIM hosted API with molmim.key (nvapi- format)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null

# molmim.key 우선, 없으면 ngc.key
if [ -f "$REPO_ROOT/molmim.key" ]; then
  API_KEY=$(cat "$REPO_ROOT/molmim.key")
  echo "Using: molmim.key"
elif [ -f "$REPO_ROOT/ngc.key" ]; then
  API_KEY=$(cat "$REPO_ROOT/ngc.key")
  echo "Using: ngc.key"
else
  echo "ERROR: No key file found in $REPO_ROOT"
  exit 1
fi
echo "API key loaded"

echo ""
echo "=== Test: /generate endpoint ==="
curl -s -w "\nHTTP_STATUS: %{http_code}\n" \
  -X POST \
  "https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"smi": "CCO", "algorithm": "none", "num_molecules": 3, "particles": 8, "scaled_radius": 1.0}' 2>&1
