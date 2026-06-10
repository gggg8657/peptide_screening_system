#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true
cd "$REPO_ROOT/bionemo"

python -c "
from esmfold_client import get_client
client = get_client()
print(f'URL: {client.base_url}')

# Test with short peptide
try:
    result = client.predict('MPITGGLVSLRRKAELSRRYLE')
    print(f'Result type: {type(result)}')
    if isinstance(result, dict):
        print(f'Keys: {list(result.keys())}')
        for k, v in result.items():
            print(f'  {k}: {str(v)[:200]}')
    elif isinstance(result, str):
        print(f'String result (first 300 chars): {result[:300]}')
except Exception as e:
    print(f'Error: {e}')
    # Try without /predict
    try:
        import requests
        url = client.base_url
        resp = requests.post(url, headers=client.headers, json={'sequence': 'MPITGGLVSLRRKAELSRRYLE'}, timeout=60)
        print(f'Direct POST status: {resp.status_code}')
        print(f'Direct POST result: {resp.text[:300]}')
    except Exception as e2:
        print(f'Direct POST error: {e2}')
" 2>&1
