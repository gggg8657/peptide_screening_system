#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true
cd "$REPO_ROOT/bionemo"

python -c "
from diffdock_client import get_client
client = get_client()
print('DiffDock Client initialized')
print(f'  Base URL: {client.base_url}')

# 간단 테스트: SSTR2 + 에탄올
from pathlib import Path
receptor = Path('../results/sstr2_docking/sstr2_receptor.pdb')
print(f'  Receptor: {receptor} (exists={receptor.exists()})')

try:
    result = client.dock_smiles(receptor, 'CCO', num_poses=3)
    print(f'  결과 타입: {type(result)}')
    print(f'  결과 키: {list(result.keys()) if isinstance(result, dict) else \"N/A\"}')
    # 결과 일부 출력
    for k, v in result.items():
        val_str = str(v)[:200]
        print(f'  {k}: {val_str}')
except Exception as e:
    print(f'  오류: {e}')
" 2>&1
