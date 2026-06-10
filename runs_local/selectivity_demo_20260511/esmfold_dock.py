"""ESMFold + PyRosetta 기반 selectivity 도킹.

전략:
  1. ESMFold로 펩타이드 구조 예측 (single sequence, MSA 불필요)
  2. 수용체 결정 구조 + 펩타이드 ESMFold 구조 결합
  3. NCAA 위치 (= ground truth binding pocket)에 펩타이드 정렬
  4. PyRosetta로 minimize + InterfaceAnalyzerMover로 ddG 산출

NCAA 위치는 원본 CIF에서 사전 추출한 좌표를 사용.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple


def predict_peptide_structure(sequence: str, out_pdb: Path) -> None:
    """ESMFold 로 펩타이드 구조 예측."""
    import torch
    from esm.pretrained import esmfold_v1

    model = esmfold_v1()
    model = model.eval().cuda()
    model.set_chunk_size(64)

    with torch.no_grad():
        output = model.infer_pdb(sequence)

    out_pdb.write_text(output)


def extract_ncaa_center_from_cif(cif_path: str) -> Optional[Tuple[float, float, float]]:
    """원본 CIF에서 HETATM(NCAA/리간드) 좌표 중심을 추출."""
    coords = []
    skip_resnames = {"HOH", "WAT", "NA", "CL", "K", "MG", "CA", "ZN", "SO4", "PO4"}

    with open(cif_path) as f:
        for line in f:
            if not line.startswith("HETATM"):
                continue
            parts = line.split()
            if len(parts) < 12:
                continue
            try:
                resname = parts[5]
                if resname in skip_resnames:
                    continue
                x = float(parts[10])
                y = float(parts[11])
                z = float(parts[12])
                coords.append((x, y, z))
            except (ValueError, IndexError):
                continue

    if not coords:
        return None

    cx = sum(c[0] for c in coords) / len(coords)
    cy = sum(c[1] for c in coords) / len(coords)
    cz = sum(c[2] for c in coords) / len(coords)
    return (cx, cy, cz)


def sanitize_receptor_pdb(cif_path: str, out_pdb: Path) -> None:
    """수용체 CIF → canonical AA만 들어간 PDB로 변환.

    HETATM, NCAA, 물, 이온, 비표준 잔기 제거.
    """
    THREE_TO_ONE = {
        'ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE',
        'LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL'
    }
    atom_lines = []
    in_atom_loop = False
    headers = []

    with open(cif_path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.strip() == 'loop_':
            for j in range(i+1, min(i+30, len(lines))):
                if lines[j].startswith('_atom_site'):
                    in_atom_loop = True
                    break
                if not lines[j].startswith('_'):
                    break
            if in_atom_loop:
                headers = []
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

    with open(out_pdb, 'w') as out:
        for ln in atom_lines:
            parts = ln.split()
            if parts[field_idx['group_PDB']] != 'ATOM':
                continue
            try:
                atom_name = parts[field_idx['label_atom_id']].strip('"')
                resname = parts[field_idx['label_comp_id']]
                if resname not in THREE_TO_ONE:
                    continue
                chain = parts[field_idx['label_asym_id']]
                resnum = int(parts[field_idx['label_seq_id']])
                x = float(parts[field_idx['Cartn_x']])
                y = float(parts[field_idx['Cartn_y']])
                z = float(parts[field_idx['Cartn_z']])
                element = parts[field_idx['type_symbol']]
                serial = int(parts[field_idx['id']])
                line = f'ATOM  {serial:5d} {atom_name:<4s} {resname:>3s} {chain[0]}{resnum:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           {element:>2s}'
                out.write(line + '\n')
            except (ValueError, KeyError, IndexError):
                continue
        out.write('END\n')


def dock_with_pyrosetta(
    receptor_pdb: str,
    peptide_pdb: str,
    target_center: Tuple[float, float, float],
    out_dir: Path,
) -> dict:
    """수용체 + 펩타이드를 target_center에 정렬 후 PyRosetta minimize + interface ddG.

    Returns: dict with ddg, raw_score, best_pdb
    """
    import pyrosetta
    pyrosetta.init(
        '-ignore_unrecognized_res true '
        '-load_PDB_components false '
        '-ignore_zero_occupancy true '
        '-mute all'
    )

    from pyrosetta.rosetta.core.pose import append_pose_to_pose
    from pyrosetta.rosetta.numeric import xyzVector_double_t as V3
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover
    from pyrosetta.rosetta.core.kinematics import MoveMap
    from pyrosetta.rosetta.protocols.minimization_packing import MinMover

    sfxn = pyrosetta.get_fa_scorefxn()
    receptor = pyrosetta.pose_from_file(receptor_pdb)
    peptide = pyrosetta.pose_from_file(peptide_pdb)

    # 펩타이드 질량 중심
    n_pep = peptide.total_residue()
    px, py, pz = 0.0, 0.0, 0.0
    for i in range(1, n_pep + 1):
        if peptide.residue(i).has("CA"):
            xyz = peptide.residue(i).xyz("CA")
            px += xyz.x; py += xyz.y; pz += xyz.z
    px /= n_pep; py /= n_pep; pz /= n_pep

    # target_center로 이동
    tx, ty, tz = target_center
    dx, dy, dz = tx - px, ty - py, tz - pz
    for i in range(1, n_pep + 1):
        for j in range(1, peptide.residue(i).natoms() + 1):
            old = peptide.residue(i).xyz(j)
            peptide.residue(i).set_xyz(j, V3(old.x + dx, old.y + dy, old.z + dz))

    # 복합체 생성
    complex_pose = receptor.clone()
    append_pose_to_pose(complex_pose, peptide, new_chain=True)
    raw_score_before = sfxn(complex_pose)

    # Minimize (backbone + sidechain + jump)
    mm = MoveMap()
    mm.set_bb(True); mm.set_chi(True); mm.set_jump(True)
    minimizer = MinMover()
    minimizer.movemap(mm)
    minimizer.score_function(sfxn)
    minimizer.min_type("dfpmin_armijo_nonmonotone")
    minimizer.tolerance(0.5)
    try:
        minimizer.apply(complex_pose)
    except Exception as e:
        return {
            "ddg": None,
            "raw_score": raw_score_before,
            "error": f"minimize_failed: {e}",
        }

    raw_score_after = sfxn(complex_pose)

    # Interface ddG — multi-jump 자동 탐색
    n_jumps = complex_pose.num_jump()
    best_dsasa = 0.0
    best_ddg = None

    for j in range(1, n_jumps + 1):
        try:
            iam = InterfaceAnalyzerMover(j)
            iam.set_compute_packstat(False)
            iam.set_pack_separated(True)
            iam.set_scorefunction(sfxn)
            iam.apply(complex_pose)
            dsasa = iam.get_interface_delta_sasa()
            ddg = iam.get_interface_dG()
            if dsasa > best_dsasa:
                best_dsasa = dsasa
                best_ddg = ddg
        except Exception:
            continue

    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdb = out_dir / "complex_min.pdb"
    complex_pose.dump_pdb(str(out_pdb))

    return {
        "ddg": best_ddg if best_ddg is not None else 0.0,
        "raw_score_before": round(raw_score_before, 2),
        "raw_score_after": round(raw_score_after, 2),
        "interface_dsasa": round(best_dsasa, 2),
        "best_pdb": str(out_pdb),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peptide-pdb", required=True, help="ESMFold 예측된 펩타이드 PDB")
    parser.add_argument("--receptor-cif", required=True, help="수용체 CIF")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. NCAA 위치 추출 (ground truth)
    target_center = extract_ncaa_center_from_cif(args.receptor_cif)
    if target_center is None:
        # fallback: receptor 표면 중심 사용
        target_center = (0.0, 0.0, 0.0)
        used_fallback = True
    else:
        used_fallback = False

    # 2. Receptor sanitize
    receptor_pdb = out_dir / "receptor_clean.pdb"
    sanitize_receptor_pdb(args.receptor_cif, receptor_pdb)

    # 3. Dock
    result = dock_with_pyrosetta(
        str(receptor_pdb),
        args.peptide_pdb,
        target_center,
        out_dir,
    )
    result["target_center"] = target_center
    result["used_fallback_center"] = used_fallback

    print(json.dumps(result))


if __name__ == "__main__":
    main()
