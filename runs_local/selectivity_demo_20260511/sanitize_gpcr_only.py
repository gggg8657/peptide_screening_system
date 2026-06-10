"""GPCR chain 단독 추출 — Round 2.

Round 1 결함: receptor_clean.pdb 가 G-protein/scFv 등 부속 chain까지 포함.
해결: 각 PDB에서 GPCR chain만 추출 + NCAA HETATM은 그대로 binding site center 계산.
"""
import json
import sys
from pathlib import Path


def extract_single_chain_pdb(cif_path: str, target_chain: str, out_pdb: Path) -> int:
    """CIF에서 지정 chain의 canonical AA만 PDB로 dump."""
    THREE = {
        'ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE',
        'LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL'
    }

    atom_lines = []
    headers = []
    in_loop = False

    with open(cif_path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.strip() == 'loop_':
            for j in range(i+1, min(i+30, len(lines))):
                if lines[j].startswith('_atom_site'):
                    in_loop = True
                    break
                if not lines[j].startswith('_'):
                    break
            if in_loop:
                k = i + 1
                while k < len(lines) and lines[k].startswith('_atom_site'):
                    headers.append(lines[k].strip())
                    k += 1
                while k < len(lines):
                    ln = lines[k].strip()
                    if not ln or ln.startswith('#') or ln.startswith('loop_'):
                        break
                    atom_lines.append(ln)
                    k += 1
                break

    field_idx = {h.replace('_atom_site.', ''): i for i, h in enumerate(headers)}

    n_atom = 0
    with open(out_pdb, 'w') as out:
        for ln in atom_lines:
            parts = ln.split()
            try:
                if parts[field_idx['group_PDB']] != 'ATOM':
                    continue
                resname = parts[field_idx['label_comp_id']]
                if resname not in THREE:
                    continue
                chain = parts[field_idx['label_asym_id']]
                if chain != target_chain:
                    continue
                atom_name = parts[field_idx['label_atom_id']].strip('"')
                resnum = int(parts[field_idx['label_seq_id']])
                x = float(parts[field_idx['Cartn_x']])
                y = float(parts[field_idx['Cartn_y']])
                z = float(parts[field_idx['Cartn_z']])
                element = parts[field_idx['type_symbol']]
                serial = int(parts[field_idx['id']])
                line = (
                    f'ATOM  {serial:5d} {atom_name:<4s} {resname:>3s} '
                    f'{chain[0]}{resnum:4d}    '
                    f'{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           {element:>2s}'
                )
                out.write(line + '\n')
                n_atom += 1
            except (ValueError, KeyError, IndexError):
                continue
        out.write('END\n')
    return n_atom


def main():
    GPCR_CHAINS = {
        "SSTR1": ("data/somatostatin_receptor/SSTR1_9IK8.cif", "A"),
        "SSTR2": ("data/somatostatin_receptor/SSTR2_7XNA.cif", "A"),
        "SSTR3": ("data/somatostatin_receptor/SSTR3_8XIR.cif", "A"),
        "SSTR4": ("data/somatostatin_receptor/SSTR4_7XMT.cif", "A"),
        "SSTR5": ("data/somatostatin_receptor/SSTR5_8ZBJ.cif", "E"),
    }

    out_dir = Path("runs_local/selectivity_demo_20260511/receptors_gpcr_only")
    out_dir.mkdir(exist_ok=True)

    old_manifest = json.load(open("runs_local/selectivity_demo_20260511/receptor_manifest.json"))
    new_manifest = {}

    for name, (cif, chain) in GPCR_CHAINS.items():
        out_pdb = out_dir / f"{name}_gpcr.pdb"
        n_atom = extract_single_chain_pdb(cif, chain, out_pdb)
        new_manifest[name] = {
            "clean_pdb": str(out_pdb),
            "n_atom": n_atom,
            "ncaa_center": old_manifest[name].get("ncaa_center"),
            "gpcr_chain": chain,
            "round": 2,
            "improvement": "single GPCR chain only (G-protein/scFv 제거)",
        }
        center = old_manifest[name].get("ncaa_center")
        print(f"{name}: chain={chain}, atoms={n_atom}, center={center}")

    out_manifest = Path("runs_local/selectivity_demo_20260511/receptor_manifest_v2.json")
    out_manifest.write_text(json.dumps(new_manifest, indent=2, default=str))
    print(f"\nSaved: {out_manifest}")


if __name__ == "__main__":
    main()
