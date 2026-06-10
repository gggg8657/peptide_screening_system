"""Approach 1: FlexPepDock 본격 적용.

차이점 (vs Round 1/2):
  - FlexPepDockingProtocol (lowres + highres) 사용
  - nstruct=10 (이전 3)
  - GPCR chain only receptor (Round 2 manifest 사용)
"""
import argparse
import json
import random
from pathlib import Path


def dock_pair(cid: str, pep_seq: str, receptor_pdb: str, target_center: tuple, out_dir: Path, nstruct: int = 10) -> dict:
    import pyrosetta
    from pyrosetta.rosetta.core.pose import append_pose_to_pose
    from pyrosetta.rosetta.numeric import xyzVector_double_t as V3
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover
    from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol
    from pyrosetta.rosetta.protocols.relax import FastRelax

    sfxn = pyrosetta.get_fa_scorefxn()
    receptor = pyrosetta.pose_from_file(receptor_pdb)

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
            scores.append({"trial": trial, "error": f"fpd: {e}"})
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
        "approach": "flexpep_full",
        "nstruct": nstruct,
        "ddg": best_ddg,
        "best_dsasa": best_dsasa,
        "trials": scores[:30],
        "best_pdb": str(pdb_out) if pdb_out else None,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", required=True)
    p.add_argument("--manifest", required=True)
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
    recs = json.load(open(args.manifest))
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    results = []
    for ci, cand in enumerate(cands):
        pep_seq = cand["seq"]
        cid = f"cand{ci:02d}_{pep_seq}"
        for rname, rinfo in recs.items():
            center = rinfo.get("ncaa_center")
            if not center:
                continue
            sub = out_root / cid / rname
            print(f"FLEXPEP: {cid} × {rname}", flush=True)
            try:
                r = dock_pair(cid, pep_seq, rinfo["clean_pdb"], tuple(center), sub, args.nstruct)
                r["receptor"] = rname
                results.append(r)
                print(f"   ddg={r.get('ddg')} dsasa={r.get('best_dsasa')}", flush=True)
            except Exception as e:
                results.append({"candidate_id": cid, "receptor": rname, "error": str(e)})
                print(f"   ERROR: {e}", flush=True)

    with open(out_root / "all_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_root}/all_results.json")


if __name__ == "__main__":
    main()
