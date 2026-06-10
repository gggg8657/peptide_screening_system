#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true
cd "$REPO_ROOT/bionemo"

python -c "
import json
from pathlib import Path
from esmfold_client import get_client as get_esmfold
from datetime import datetime

OUTPUT_DIR = Path('../results/sstr2_docking/arm3_denovo')

# 이전 ProteinMPNN 결과에서 서열 로드
designed = [
    {'backbone_idx': 0, 'seq_idx': 0, 'sequence': 'MPITGGLVSLRRKAELSRRYLE'},
    {'backbone_idx': 0, 'seq_idx': 1, 'sequence': 'TPLTGGEAQLVRYASLARRYLE'},
    {'backbone_idx': 0, 'seq_idx': 2, 'sequence': 'AGLTGGLAAYREYCRLARRLLE'},
    {'backbone_idx': 0, 'seq_idx': 3, 'sequence': 'SGLTGGLLALRRYAELARRYLE'},
    {'backbone_idx': 1, 'seq_idx': 0, 'sequence': 'MAALGLLLFEYAEQ'},
    {'backbone_idx': 1, 'seq_idx': 1, 'sequence': 'AAALGLLLFEAAEQ'},
    {'backbone_idx': 1, 'seq_idx': 2, 'sequence': 'AAAFGELLFEASEQ'},
    {'backbone_idx': 1, 'seq_idx': 3, 'sequence': 'MEFLGLLMFEYDEQ'},
    {'backbone_idx': 2, 'seq_idx': 0, 'sequence': 'SALIWARGEGE'},
    {'backbone_idx': 2, 'seq_idx': 1, 'sequence': 'PALIWAEGRGE'},
    {'backbone_idx': 2, 'seq_idx': 2, 'sequence': 'SPLIWARGDGE'},
    {'backbone_idx': 2, 'seq_idx': 3, 'sequence': 'SGLIWARGGGR'},
    {'backbone_idx': 3, 'seq_idx': 0, 'sequence': 'AALARTIRADFRAQQQA'},
    {'backbone_idx': 3, 'seq_idx': 1, 'sequence': 'AALWQTILTRFRRQQEE'},
    {'backbone_idx': 3, 'seq_idx': 2, 'sequence': 'AALARTIAARFRKELEA'},
    {'backbone_idx': 3, 'seq_idx': 3, 'sequence': 'AALFSTARTRFRLQREE'},
]

print(f'ESMFold 검증: {len(designed)}개 서열')

esmfold = get_esmfold()
verified = []

for d in designed:
    seq = d['sequence']
    label = f\"bb{d['backbone_idx']:02d}_seq{d['seq_idx']}\"
    print(f'\n[{label}] {seq}')
    try:
        result = esmfold.predict(seq)
        pdb = None
        if isinstance(result, dict) and 'pdbs' in result:
            pdb = result['pdbs'][0] if result['pdbs'] else None
        
        if pdb:
            # pLDDT from B-factors
            import re
            bfactors = []
            for line in pdb.split('\n'):
                if line.startswith('ATOM'):
                    try:
                        bf = float(line[60:66].strip())
                        bfactors.append(bf)
                    except:
                        pass
            plddt = sum(bfactors) / len(bfactors) if bfactors else None
            d['plddt'] = plddt
            
            pdb_path = OUTPUT_DIR / f'esmfold_{label}.pdb'
            pdb_path.write_text(pdb)
            d['esmfold_pdb'] = str(pdb_path)
            verified.append(d)
            print(f'  -> pLDDT={plddt:.1f}  saved: {pdb_path.name}' if plddt else f'  -> structure saved')
        else:
            print(f'  -> No PDB in result')
    except Exception as e:
        print(f'  -> Error: {e}')

# 결과 저장
output = OUTPUT_DIR / f'arm3_final_{datetime.now():%Y%m%d_%H%M%S}.json'
save = {
    'pipeline': 'Arm 3: De Novo Peptide Binder Design (RFdiffusion + ProteinMPNN + ESMFold)',
    'total_backbones': 4,
    'total_designed': len(designed),
    'verified': len(verified),
    'designs': [{
        'backbone_idx': d['backbone_idx'],
        'seq_idx': d['seq_idx'],
        'binder_sequence': d['sequence'],
        'plddt': d.get('plddt'),
        'esmfold_pdb': d.get('esmfold_pdb', ''),
    } for d in verified],
    'timestamp': datetime.now().isoformat(),
}
output.write_text(json.dumps(save, indent=2))

print(f'\n=== Arm 3 Final Summary ===')
print(f'  Designed: {len(designed)} | Verified: {len(verified)}')
# Sort by plddt
verified.sort(key=lambda x: x.get('plddt', 0), reverse=True)
for d in verified:
    p = f'pLDDT={d[\"plddt\"]:.1f}' if d.get('plddt') else 'N/A'
    print(f'  bb{d[\"backbone_idx\"]:02d}_seq{d[\"seq_idx\"]}: {d[\"sequence\"]:25s} {p}')
print(f'Results: {output}')
print(f'\nNext: Submit top sequences + SSTR2 to AlphaFold3 Server for complex prediction')
" 2>&1
