"""Approach 2: Pharmacophore alignment.

차이점 (vs Round 1/2):
  - 펩타이드 전체 중심 대신, SST-14의 pharmacophore (NFFWKT, pos5-10)만 NCAA 중심에 정렬
  - 위치 5-10의 CA 평균 = NCAA 중심
  - 나머지 잔기 (1-4, 11-14)는 자유롭게 따라옴
  - MinMover (sidechain + jump)
  - nstruct=5
"""
import argparse
import json
import random
from pathlib import Path


def pharma_align_dock(cid: str, pep_seq: str, receptor_pdb: str, target_center: tuple, out_dir: Path, nstruct: int = 5) -> dict:
    import pyrosetta
    from pyrosetta.rosetta.core.pose import append_pose_to_pose
    from pyrosetta.rosetta.numeric import xyzVector_double_t as V3
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover
    from pyrosetta.rosetta.core.kinematics import MoveMap
    from pyrosetta.rosetta.protocols.minimization_packing import MinMover
    from pyrosetta.rosetta.protocols.relax import FastRelax

    sfxn = pyrosetta.get_fa_scorefxn()
    receptor = pyrosetta.pose_from_file(receptor_pdb)

    pep_tmpl = pyrosetta.pose_from_sequence(pep_seq, "fa_standard")
    rel = FastRelax(); rel.set_scorefxn(sfxn); rel.max_iter(30)
    try:
        rel.apply(pep_tmpl)
    except Exception as e:
        return {"error": f"relax: {e}"}

    n_pep = pep_tmpl.total_residue()
    # pharmacophore 위치 — 1-indexed
    if n_pep >= 10:
        pharma_positions = list(range(5, 11))  # 5..10
    else:
        pharma_positions = list(range(1, n_pep + 1))

    tx, ty, tz = target_center
    best_ddg, best_dsasa, best_pose = None, 0.0, None
    scores = []

    for trial in range(nstruct):
        peptide = pep_tmpl.clone()

        # pharmacophore CA 평균
        ppx, ppy, ppz = 0.0, 0.0, 0.0
        cnt = 0
        for i in pharma_positions:
            if 1 <= i <= peptide.total_residue() and peptide.residue(i).has("CA"):
                xyz = peptide.residue(i).xyz("CA")
                ppx += xyz.x; ppy += xyz.y; ppz += xyz.z
                cnt += 1
        if cnt == 0:
            continue
        ppx /= cnt; ppy /= cnt; ppz /= cnt

        jit = 3.0
        dx = tx - ppx + random.uniform(-jit, jit)
        dy = ty - ppy + random.uniform(-jit, jit)
        dz = tz - ppz + random.uniform(-jit, jit)
        for i in range(1, peptide.total_residue() + 1):
            for j in range(1, peptide.residue(i).natoms() + 1):
                old = peptide.residue(i).xyz(j)
                peptide.residue(i).set_xyz(j, V3(old.x + dx, old.y + dy, old.z + dz))

        complex_pose = receptor.clone()
        append_pose_to_pose(complex_pose, peptide, new_chain=True)

        mm = MoveMap()
        mm.set_bb(False); mm.set_chi(True); mm.set_jump(True)
        mmin = MinMover()
        mmin.movemap(mm); mmin.score_function(sfxn)
        mmin.min_type("dfpmin_armijo_nonmonotone"); mmin.tolerance(0.5)
        try:
            mmin.apply(complex_pose)
        except Exception:
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
        "approach": "pharma_align",
        "pharma_positions": pharma_positions,
        "nstruct": nstruct,
        "ddg": best_ddg,
        "best_dsasa": best_dsasa,
        "trials": scores[:20],
        "best_pdb": str(pdb_out) if pdb_out else None,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--nstruct", type=int, default=5)
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
            print(f"PHARMA: {cid} × {rname}", flush=True)
            try:
                r = pharma_align_dock(cid, pep_seq, rinfo["clean_pdb"], tuple(center), sub, args.nstruct)
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
