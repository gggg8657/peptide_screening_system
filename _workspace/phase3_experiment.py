"""Phase 3 실험 — modification conflict matrix + PyRosetta SST-14 score.

End-to-End 사이클의 Phase 3.
- 다양한 modification 조합 12개에 대해 conflict checker 결과 매트릭스
- PyRosetta로 SST-14 native 시퀀스의 ref2015 score 1회 (도킹 X, 빠른 평가만)
- 결과를 _workspace/06_experiment_results.md로 보존
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_local.scripts.modification_conflict import check_conflicts  # noqa: E402

SST14 = "AGCKNFFWKTFTSC"  # AGCKNFFWKTFTSC (Cys3-Cys14 SS bond, FWKT pharmacophore)

# ---------------------------------------------------------------------------
# 1. modification 조합 매트릭스 (12 cases)
# ---------------------------------------------------------------------------

TEST_CASES = [
    # name, modifications, expected (passes if no ERROR conflict)
    ("FA on Lys4 only", [{"mod_type": "fatty_acid", "position": 4}], True),
    ("FA + PEG on same Lys4 (C-01)", [
        {"mod_type": "fatty_acid", "position": 4},
        {"mod_type": "pegylation", "position": 4}
    ], False),
    ("FA on Trp7 (C-02)", [{"mod_type": "fatty_acid", "position": 7}], False),
    ("FA on N-term Ala1 (C-02 exception)", [{"mod_type": "fatty_acid", "position": 1}], True),
    ("D-Gly2 no-op (C-03)", [{"mod_type": "d_amino_acid", "position": 2}], "warning"),
    # NOTE: Phase 5 fix — C-04는 WARNING → ERROR 격상 (Veber 1978, Pellegrini 1999)
    ("D-Cys3 SS risk (C-04)", [{"mod_type": "d_amino_acid", "position": 3}], False),
    # NOTE: Phase 5 fix — _RULES 순서 변경 후 position=0이 C-06으로 먼저 catch됨 (의도된 동작)
    ("Duplicate cyclization (C-05)", [{"mod_type": "cyclization", "position": 1}], "warning"),
    ("Position out of range (C-06)", [{"mod_type": "fatty_acid", "position": 99}], False),
    ("FA Lys4 + PEG Cys3-N-term-replacement (combo, valid)", [
        {"mod_type": "fatty_acid", "position": 4},
        {"mod_type": "pegylation", "position": 1}
    ], True),
    ("D-Phe6 substitution OK", [{"mod_type": "d_amino_acid", "position": 6}], True),
    ("Substitution Lys4 OK", [{"mod_type": "substitution", "position": 4}], True),
    ("3 modifications mixed (FA+D-Phe6+sub-Trp7)", [
        {"mod_type": "fatty_acid", "position": 4},
        {"mod_type": "d_amino_acid", "position": 6},
        {"mod_type": "substitution", "position": 7}
    ], True),
]


def run_conflict_matrix():
    print("\n" + "=" * 70)
    print(" Modification Conflict Matrix — SST-14 (AGCKNFFWKTFTSC)")
    print("=" * 70)

    results = []
    for name, mods, expected in TEST_CASES:
        conflicts = check_conflicts(SST14, mods)
        errors = [c for c in conflicts if c.severity == "ERROR"]
        warnings = [c for c in conflicts if c.severity == "WARNING"]

        if expected is True:
            ok = len(errors) == 0
        elif expected is False:
            ok = len(errors) > 0
        elif expected == "warning":
            ok = len(warnings) > 0

        status = "PASS" if ok else "FAIL"
        marker = "+" if ok else "X"

        result = {
            "case": name,
            "mods": mods,
            "expected": expected,
            "errors": [{"rule": c.rule_id, "msg": c.description} for c in errors],
            "warnings": [{"rule": c.rule_id, "msg": c.description} for c in warnings],
            "status": status,
        }
        results.append(result)

        print(f"  [{marker}] {name:60s} {status}")
        for c in errors + warnings:
            print(f"       {c.severity:7s} {c.rule_id}: {c.description[:70]}")

    n_pass = sum(1 for r in results if r["status"] == "PASS")
    print(f"\n  Total: {n_pass}/{len(TEST_CASES)} PASS")
    return results, n_pass, len(TEST_CASES)


# ---------------------------------------------------------------------------
# 2. PyRosetta SST-14 score (가벼운 평가)
# ---------------------------------------------------------------------------


def run_pyrosetta_score():
    print("\n" + "=" * 70)
    print(" PyRosetta SST-14 score (FastRelax + ref2015)")
    print("=" * 70)

    try:
        import pyrosetta
    except ImportError as e:
        print(f"  SKIP — PyRosetta not importable: {e}")
        return None

    pyrosetta.init(extra_options="-mute all -ignore_unrecognized_res", silent=True)

    # SST-14 시퀀스에서 pose 생성
    pose = pyrosetta.pose_from_sequence(SST14)
    n_res = pose.total_residue()
    print(f"  Loaded SST-14 pose: {n_res} residues")

    # ref2015 score
    scorefxn = pyrosetta.create_score_function("ref2015")
    initial_score = scorefxn(pose)
    print(f"  Initial ref2015 score (linear, no SS): {initial_score:.2f}")

    # SS bond 형성 — Cys3-Cys14 (1-indexed → res3, res14)
    # VR-cycle-03 fix: DisulfideInsertionMover.set_residue_ids는 존재하지 않음.
    # 올바른 API는 core.conformation.form_disulfide(pose.conformation(), 3, 14)
    try:
        from pyrosetta.rosetta.core import conformation
        conformation.form_disulfide(pose.conformation(), 3, 14)
        ss_score = scorefxn(pose)
        print(f"  With Cys3-Cys14 SS bond (no min):  {ss_score:.2f}")
    except Exception as e:
        print(f"  SS bond formation failed: {e}")
        ss_score = None

    # 짧은 minimization
    try:
        from pyrosetta.rosetta.protocols.minimization_packing import MinMover
        from pyrosetta.rosetta.core.kinematics import MoveMap
        mm = MoveMap()
        mm.set_bb(True)
        mm.set_chi(True)
        minmover = MinMover()
        minmover.movemap(mm)
        minmover.score_function(scorefxn)
        minmover.min_type("lbfgs_armijo_nonmonotone")
        minmover.tolerance(0.01)
        minmover.apply(pose)
        final_score = scorefxn(pose)
        print(f"  After MinMover:                    {final_score:.2f}")
    except Exception as e:
        print(f"  Minimization skipped: {e}")
        final_score = ss_score

    return {
        "sequence": SST14,
        "n_residues": n_res,
        "initial_score": float(initial_score),
        "ss_bond_score": float(ss_score) if ss_score is not None else None,
        "minimized_score": float(final_score) if final_score is not None else None,
    }


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------


def main():
    print("Phase 3 Experiment — modification_conflict + PyRosetta SST-14")

    conflict_results, n_pass, n_total = run_conflict_matrix()
    pyrosetta_result = run_pyrosetta_score()

    out = {
        "conflict_matrix": {
            "results": conflict_results,
            "summary": f"{n_pass}/{n_total} PASS",
            "n_pass": n_pass,
            "n_total": n_total,
        },
        "pyrosetta_sst14": pyrosetta_result,
    }
    out_path = PROJECT_ROOT / "_workspace" / "06_experiment_raw.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n  Raw results saved: {out_path}")


if __name__ == "__main__":
    main()
