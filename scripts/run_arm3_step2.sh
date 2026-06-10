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
from proteinmpnn_client import get_client as get_proteinmpnn
from esmfold_client import get_client as get_esmfold
from datetime import datetime

OUTPUT_DIR = Path('../results/sstr2_docking/arm3_denovo')

# 기존 RFdiffusion 백본 로드
backbones = []
for f in sorted(OUTPUT_DIR.glob('backbone_*.pdb')):
    pdb = f.read_text()
    idx = int(f.stem.split('_')[1])
    backbones.append({'idx': idx, 'pdb_content': pdb, 'pdb_path': str(f)})
    print(f'Loaded backbone {f.name} ({len(pdb)} chars)')

print(f'\n{len(backbones)} backbones loaded')

# Step 2: ProteinMPNN
mpnn = get_proteinmpnn()
designed = []
for bb in backbones:
    idx = bb['idx']
    print(f'\n[ProteinMPNN] backbone {idx:02d}:')
    try:
        result = mpnn.predict(input_pdb=bb['pdb_content'], num_seq_per_target=4, sampling_temp=0.2)
        print(f'  Result keys: {list(result.keys())}')
        
        # 응답 파싱
        sequences = []
        if isinstance(result, dict):
            for key in ['sequences', 'output', 'generated']:
                if key in result:
                    raw = result[key]
                    if isinstance(raw, str):
                        # FASTA 파싱
                        for line in raw.split('\n'):
                            if line and not line.startswith('>'):
                                sequences.append(line.strip())
                    elif isinstance(raw, list):
                        sequences = raw
                    break
        
        if not sequences:
            # 전체 결과 출력
            print(f'  Full result: {str(result)[:500]}')
        
        for j, seq in enumerate(sequences):
            designed.append({'backbone_idx': idx, 'seq_idx': j, 'sequence': seq})
            print(f'  seq{j}: {seq[:50]}...' if len(seq) > 50 else f'  seq{j}: {seq}')
    except Exception as e:
        print(f'  Error: {e}')

print(f'\nTotal sequences: {len(designed)}')

# Step 3: ESMFold
if designed:
    esmfold = get_esmfold()
    verified = []
    for d in designed[:8]:  # 최대 8개만
        seq = d['sequence']
        label = f\"bb{d['backbone_idx']:02d}_seq{d['seq_idx']}\"
        print(f'\n[ESMFold] {label}: {seq[:30]}...')
        try:
            result = esmfold.predict(seq)
            pdb = None
            plddt = None
            if isinstance(result, dict):
                plddt = result.get('mean_plddt', result.get('plddt'))
                for k in ['pdbs', 'pdb', 'output']:
                    if k in result:
                        v = result[k]
                        pdb = v[0] if isinstance(v, list) else v
                        break
            d['plddt'] = plddt
            if pdb:
                pdb_path = OUTPUT_DIR / f'esmfold_{label}.pdb'
                pdb_path.write_text(pdb)
                d['esmfold_pdb'] = str(pdb_path)
            verified.append(d)
            print(f'  -> pLDDT={plddt}' if plddt else f'  -> structure generated (keys: {list(result.keys())})')
        except Exception as e:
            print(f'  -> Error: {e}')

    # 결과 저장
    output = OUTPUT_DIR / f'arm3_results_{datetime.now():%Y%m%d_%H%M%S}.json'
    save = {
        'total_backbones': len(backbones),
        'total_sequences': len(designed),
        'verified': len(verified),
        'designs': [{'backbone_idx': d['backbone_idx'], 'seq_idx': d['seq_idx'], 'sequence': d['sequence'], 'plddt': d.get('plddt')} for d in verified],
        'timestamp': datetime.now().isoformat(),
    }
    output.write_text(json.dumps(save, indent=2))
    print(f'\nResults saved: {output}')
    print(f'\n=== Summary ===')
    print(f'  Backbones: {len(backbones)}')
    print(f'  Sequences: {len(designed)}')
    print(f'  Verified: {len(verified)}')
else:
    print('No sequences to verify')
" 2>&1
