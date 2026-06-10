"""Approach 3: AlphaFold apo 수용체 + FlexPepDock 재시도.

차이점 (vs Round 2/A1):
  - 결정 구조(holo) 대신 AlphaFold 예측 apo 구조
  - apo는 ligand-free → pocket이 열려 있을 가능성
  - holo의 NCAA center를 apo 좌표계로 변환 (CA-align)
  - FlexPepDockingProtocol
"""
import argparse
import json
import random
from pathlib import Path


THREE = {
    'ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE',
    'LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL'
}


def extract_ca_from_pdb(pdb_path: str, chain: str = None):
    """PDB에서 (resnum, x, y, z, resname) 리스트 추출 (CA만, canonical만)."""
    result = []
    with open(pdb_path) as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            atom = line[12:16].strip()
            if atom != "CA":
                continue
            resname = line[17:20].strip()
            if resname not in THREE:
                continue
            c = line[21]
            if chain and c != chain:
                continue
            try:
                resnum = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                result.append((resnum, x, y, z, resname))
            except ValueError:
                continue
    return result


def kabsch_align(P, Q):
    """P를 Q에 align — return (R, t, rmsd)."""
    import numpy as np
    P = np.asarray(P, dtype=float)
    Q = np.asarray(Q, dtype=float)
    cp = P.mean(axis=0); cq = Q.mean(axis=0)
    P0 = P - cp; Q0 = Q - cq
    H = P0.T @ Q0
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    t = cq - R @ cp
    P_aligned = (R @ P.T).T + t
    rmsd = float(np.sqrt(((P_aligned - Q) ** 2).sum() / len(P)))
    return R, t, rmsd


def transform_point(point, R, t):
    import numpy as np
    return tuple((R @ np.asarray(point) + t).tolist())


def align_and_get_center(holo_pdb: str, apo_pdb: str, holo_ncaa_center: tuple, holo_chain: str = None):
    """Holo CA를 apo CA에 align → apo 좌표계의 NCAA center 반환."""
    holo_ca = extract_ca_from_pdb(holo_pdb, holo_chain)
    apo_ca = extract_ca_from_pdb(apo_pdb, "A")

    # 공통 잔기 번호로 매칭
    holo_dict = {r[0]: r[1:4] for r in holo_ca}
    apo_dict = {r[0]: r[1:4] for r in apo_ca}
    common = sorted(set(holo_dict) & set(apo_dict))
    if len(common) < 50:
        return None, f"insufficient common residues: {len(common)}"

    P = [holo_dict[i] for i in common]  # holo CA
    Q = [apo_dict[i] for i in common]   # apo CA

    R, t, rmsd = kabsch_align(P, Q)
    transformed_center = transform_point(holo_ncaa_center, R, t)
    return transformed_center, {"n_common": len(common), "rmsd": rmsd}


def dock_pair(cid: str, pep_seq: str, apo_pdb: str, target_center: tuple, out_dir: Path, nstruct: int = 10):
    import pyrosetta
    from pyrosetta.rosetta.core.pose import append_pose_to_pose
    from pyrosetta.rosetta.numeric import xyzVector_double_t as V3
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover
    from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol
    from pyrosetta.rosetta.protocols.relax import FastRelax

    sfxn = pyrosetta.get_fa_scorefxn()
    receptor = pyrosetta.pose_from_file(apo_pdb)

    pep_tmpl = pyrosetta.pose_from_sequence(pep_seq, "fa_standard")
    rel = FastRelax(); rel.set_scorefxn(sfxn); rel.max_iter(30)
    try:
        rel.apply(pep_tmpl)
    except Exception as e:
        return {"error": f"relax: {e}"}

    tx, ty, tz = target_center
    best_ddg, best_dsasa, best_pose = None, 0.0, None
    scores = []

    for trial in range(nstruct):
        peptide = pep_tmpl.clone()
        n_pep = peptide.total_residue()
        px, py, pz = 0.0, 0.0, 0.0
        for i in range(1, n_pep + 1):
            xyz = peptide.residue(i).xyz("CA")
            px += xyz.x; py += xyz.y; pz += xyz.z
        px /= n_pep; py /= n_pep; pz /= n_pep

        jit = 3.0
        dx = tx - px + random.uniform(-jit, jit)
        dy = ty - py + random.uniform(-jit, jit)
        dz = tz - pz + random.uniform(-jit, jit)
        for i in range(1, n_pep + 1):
            for j in range(1, peptide.residue(i).natoms() + 1):
                old = peptide.residue(i).xyz(j)
                peptide.residue(i).set_xyz(j, V3(old.x + dx, old.y + dy, old.z + dz))

        complex_pose = receptor.clone()
        append_pose_to_pose(complex_pose, peptide, new_chain=True)

        try:
            fpd = FlexPepDockingProtocol()
            fpd.apply(complex_pose)
        except Exception as e:
            scores.append({"trial": trial, "error": str(e)})
            continue

        for j in range(1, complex_pose.num_jump() + 1):
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
                    best_pose = complex_pose.clone()
                scores.append({"trial": trial, "jump": j, "ddg": round(ddg, 2), "dsasa": round(dsasa, 1)})
            except Exception:
                continue

    pdb_out = None
    if best_pose is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        pdb_out = out_dir / "best_complex.pdb"
        best_pose.dump_pdb(str(pdb_out))

    return {
        "candidate_id": cid,
        "peptide_seq": pep_seq,
        "approach": "alphafold_apo",
        "nstruct": nstruct,
        "ddg": best_ddg,
        "best_dsasa": best_dsasa,
        "trials": scores[:30],
        "best_pdb": str(pdb_out) if pdb_out else None,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", required=True)
    p.add_argument("--holo-manifest", required=True, help="Holo manifest (NCAA centers)")
    p.add_argument("--apo-dir", required=True, help="AlphaFold PDB directory")
    p.add_argument("--output", required=True)
    p.add_argument("--nstruct", type=int, default=10)
    args = p.parse_args()

    import pyrosetta
    pyrosetta.init(
        "-ignore_unrecognized_res true "
        "-load_PDB_components false "
        "-ignore_zero_occupancy true "
        "-no_optH true "
        "-mute all"
    )

    cands = json.load(open(args.candidates))["top10"]
    holo_recs = json.load(open(args.holo_manifest))

    # UniProt 매핑
    UNIPROT = {
        "SSTR1": "P30872", "SSTR2": "P30874", "SSTR3": "P32745",
        "SSTR4": "P31391", "SSTR5": "P35346",
    }
    apo_pdbs = {
        name: str(Path(args.apo_dir) / f"AF-{upid}-F1-model.pdb")
        for name, upid in UNIPROT.items()
    }

    # 각 receptor: holo NCAA center를 apo 좌표계로 변환
    apo_centers = {}
    print("=== Alignment ===")
    for name, holo_info in holo_recs.items():
        holo_pdb = holo_info["clean_pdb"]
        holo_center = tuple(holo_info["ncaa_center"]) if holo_info.get("ncaa_center") else None
        if holo_center is None:
            print(f"  {name}: SKIP (no center)")
            continue
        apo_center, meta = align_and_get_center(
            holo_pdb, apo_pdbs[name], holo_center, holo_chain=None,
        )
        if apo_center is None:
            print(f"  {name}: align FAILED: {meta}")
            continue
        apo_centers[name] = apo_center
        print(f"  {name}: rmsd={meta['rmsd']:.2f} n_common={meta['n_common']} center={apo_center}")

    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    # Manifest 저장 (apo-aligned)
    apo_manifest = {
        name: {
            "apo_pdb": apo_pdbs[name],
            "uniprot": UNIPROT[name],
            "ncaa_center_apo": list(apo_centers.get(name, ())) or None,
            "ncaa_center_holo": list(tuple(holo_recs[name].get("ncaa_center")) if holo_recs[name].get("ncaa_center") else ()),
        }
        for name in UNIPROT
    }
    (out_root / "apo_manifest.json").write_text(json.dumps(apo_manifest, indent=2))

    results = []
    for ci, cand in enumerate(cands):
        pep_seq = cand["seq"]
        cid = f"cand{ci:02d}_{pep_seq}"
        for rname, center in apo_centers.items():
            sub = out_root / cid / rname
            print(f"APO_DOCK: {cid} × {rname}", flush=True)
            try:
                r = dock_pair(cid, pep_seq, apo_pdbs[rname], tuple(center), sub, args.nstruct)
                r["receptor"] = rname
                results.append(r)
                print(f"   ddg={r.get('ddg')} dsasa={r.get('best_dsasa')}", flush=True)
            except Exception as e:
                results.append({"candidate_id": cid, "receptor": rname, "error": str(e)})

    with open(out_root / "all_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_root}/all_results.json")


if __name__ == "__main__":
    main()
