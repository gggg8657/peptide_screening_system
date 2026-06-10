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

print(f'{len(backbones)} backbones loaded')

# Step 2: ProteinMPNN
mpnn = get_proteinmpnn()
designed = []

for bb in backbones:
    idx = bb['idx']
    print(f'\n[ProteinMPNN] backbone {idx:02d}:')
    try:
        result = mpnn.predict(input_pdb=bb['pdb_content'], num_seq_per_target=4, sampling_temp=0.2)
        
        # mfasta 파싱: 바인더 체인 (/ 앞 부분)만 추출
        mfasta = result.get('mfasta', '')
        entries = []
        current_header = None
        current_seq_lines = []
        
        for line in mfasta.split('\n'):
            if line.startswith('>'):
                if current_header is not None:
                    seq = ''.join(current_seq_lines)
                    entries.append({'header': current_header, 'full_seq': seq})
                current_header = line[1:]
                current_seq_lines = []
            elif line.strip():
                current_seq_lines.append(line.strip())
        if current_header:
            seq = ''.join(current_seq_lines)
            entries.append({'header': current_header, 'full_seq': seq})
        
        print(f'  {len(entries)} entries in mfasta')
        
        # 첫 번째는 input (reference), 나머지가 designed
        for j, entry in enumerate(entries):
            full_seq = entry['full_seq']
            # / 로 체인 분리 -> 첫 번째가 바인더 (Chain A)
            chains = full_seq.split('/')
            binder_seq = chains[0] if chains else full_seq
            
            header_short = entry['header'][:60]
            is_input = 'input' in entry['header']
            tag = 'INPUT' if is_input else f'DESIGN'
            
            if not is_input:  # 설계된 서열만
                designed.append({
                    'backbone_idx': idx,
                    'seq_idx': j - 1,  # input 제외
                    'sequence': binder_seq,
                    'full_sequence': full_seq,
                    'header': entry['header'],
                })
            print(f'  [{tag}] binder={binder_seq[:40]} (len={len(binder_seq)})')
    except Exception as e:
        print(f'  Error: {e}')

print(f'\nTotal designed binder sequences: {len(designed)}')

# Step 3: ESMFold - 바인더 서열만 폴딩 검증
if designed:
    esmfold = get_esmfold()
    verified = []
    
    for d in designed[:8]:  # 최대 8개
        seq = d['sequence']
        label = f\"bb{d['backbone_idx']:02d}_seq{d['seq_idx']}\"
        print(f'\n[ESMFold] {label}: {seq}')
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
                if plddt is None and pdb:
                    # PDB에서 B-factor로부터 pLDDT 추출
                    import re
                    bfactors = [float(x) for x in re.findall(r'[\d.]+(?=\s+[A-Z]\s*$)', pdb[:5000]) if float(x) > 0]
                    if bfactors:
                        plddt = sum(bfactors) / len(bfactors)
                        
            d['plddt'] = plddt
            if pdb:
                pdb_path = OUTPUT_DIR / f'esmfold_{label}.pdb'
                pdb_path.write_text(pdb)
                d['esmfold_pdb'] = str(pdb_path)
            verified.append(d)
            
            plddt_str = f'pLDDT={plddt:.1f}' if plddt else f'keys={list(result.keys())}'
            print(f'  -> {plddt_str}')
        except Exception as e:
            print(f'  -> Error: {e}')
    
    # 결과 저장
    output = OUTPUT_DIR / f'arm3_final_{datetime.now():%Y%m%d_%H%M%S}.json'
    save = {
        'pipeline': 'Arm 3: De Novo Peptide Binder Design',
        'total_backbones': len(backbones),
        'total_designed': len(designed),
        'verified': len(verified),
        'designs': [{
            'backbone_idx': d['backbone_idx'],
            'seq_idx': d['seq_idx'],
            'binder_sequence': d['sequence'],
            'plddt': d.get('plddt'),
        } for d in verified],
        'timestamp': datetime.now().isoformat(),
    }
    output.write_text(json.dumps(save, indent=2))
    
    print(f'\n=== Arm 3 Final Summary ===')
    print(f'  Backbones: {len(backbones)}')
    print(f'  Designed sequences: {len(designed)}')
    print(f'  ESMFold verified: {len(verified)}')
    for d in verified:
        plddt_str = f'pLDDT={d[\"plddt\"]:.1f}' if d.get('plddt') else 'N/A'
        print(f'  bb{d[\"backbone_idx\"]:02d}_seq{d[\"seq_idx\"]}: {d[\"sequence\"]}  ({plddt_str})')
    print(f'Results: {output}')
else:
    print('No designed sequences found')
" 2>&1
