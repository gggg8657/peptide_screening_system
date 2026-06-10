#!/usr/bin/env python3
"""
flexpep_dock.py
===============
Standalone PyRosetta FlexPepDock refinement + InterfaceAnalyzer ddG script.

Called by AG_src/pipeline/step06_rosetta.py via subprocess:
    # Mode 1: Direct complex PDB input
    conda run -n bio-tools python AG_src/scripts/flexpep_dock.py \
        --input complex.pdb --output refined.pdb --protocol flexpep_refine

    # Mode 2: Reference complex + MutateResidue (preferred for variants)
    conda run -n bio-tools python AG_src/scripts/flexpep_dock.py \
        --input complex.pdb --output refined.pdb --protocol flexpep_refine \
        --reference-complex ref.pdb --target-sequence SGCKNFFWKTFTCA \
        --peptide-chain 1

stdout: JSON only (step06_rosetta.py L378 parses via json.loads)
stderr: all PyRosetta logs and diagnostics
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# PyRosetta initialization
# ---------------------------------------------------------------------------

def init_pyrosetta() -> None:
    """Initialize PyRosetta with muted output (all logs to stderr)."""
    import pyrosetta
    pyrosetta.init(
        options=(
            "-mute all -ex1 -ex2aro -ignore_unrecognized_res"
            " -flexPepDocking:pep_refine"
            " -constraints:cst_fa_weight 1.0"
        ),
        silent=True,
    )


# ---------------------------------------------------------------------------
# Complex preparation via MutateResidue
# ---------------------------------------------------------------------------

def prepare_complex_by_mutation(
    reference_pdb: str,
    target_sequence: str,
    peptide_chain: int = 1,
) -> Tuple["pyrosetta.Pose", int]:
    """Load a reference complex and mutate the peptide chain to the target sequence.

    This preserves the backbone conformation from the reference complex
    (e.g., AlphaFold3 prediction) and only changes sidechains.
    Much more reliable than assembling from separate PDBs.

    Args:
        reference_pdb: Path to the reference receptor-peptide complex.
        target_sequence: Target amino acid sequence (1-letter code).
        peptide_chain: Chain number of the peptide in the reference (1-indexed).

    Returns:
        (Pose with mutated peptide ready for FlexPepDock, resolved peptide chain index).
    """
    import pyrosetta
    from pyrosetta.rosetta.protocols.simple_moves import MutateResidue

    # 1-letter to 3-letter amino acid code mapping (MutateResidue requires 3-letter)
    _AA1TO3 = {
        'A': 'ALA', 'C': 'CYS', 'D': 'ASP', 'E': 'GLU', 'F': 'PHE',
        'G': 'GLY', 'H': 'HIS', 'I': 'ILE', 'K': 'LYS', 'L': 'LEU',
        'M': 'MET', 'N': 'ASN', 'P': 'PRO', 'Q': 'GLN', 'R': 'ARG',
        'S': 'SER', 'T': 'THR', 'V': 'VAL', 'W': 'TRP', 'Y': 'TYR',
    }

    pose = pyrosetta.pose_from_pdb(reference_pdb)

    # Collect chain residues and sequences from pose (chain index: 1-indexed)
    chain_residues: Dict[int, List[int]] = {}
    for i in range(1, pose.total_residue() + 1):
        cid = pose.chain(i)
        chain_residues.setdefault(cid, []).append(i)

    if not chain_residues:
        print("WARNING: No chains found in reference pose", file=sys.stderr)
        return pose, peptide_chain

    chain_lengths = {cid: len(res) for cid, res in chain_residues.items()}
    target_len = len(target_sequence)
    best_chain = min(chain_lengths, key=lambda cid: (abs(chain_lengths[cid] - target_len), chain_lengths[cid]))

    resolved_chain = peptide_chain
    if resolved_chain not in chain_residues:
        print(
            f"WARNING: Requested chain {peptide_chain} not found. Auto-selected chain {best_chain}.",
            file=sys.stderr,
        )
        resolved_chain = best_chain
    else:
        req_len = chain_lengths[resolved_chain]
        # If requested chain is far longer than target peptide, prefer the closest chain.
        if req_len > max(target_len + 10, target_len * 2) and best_chain != resolved_chain:
            print(
                f"WARNING: Requested chain {peptide_chain} length={req_len} mismatches target_len={target_len}. "
                f"Auto-switched to chain {best_chain} length={chain_lengths[best_chain]}.",
                file=sys.stderr,
            )
            resolved_chain = best_chain

    pep_residues = chain_residues[resolved_chain]

    if not pep_residues:
        print(
            f"WARNING: No residues found for chain {peptide_chain}",
            file=sys.stderr,
        )
        return pose, resolved_chain

    # Get reference peptide sequence
    ref_seq = "".join(pose.residue(i).name1() for i in pep_residues)
    print(
        f"Reference peptide (chain {resolved_chain}): {ref_seq} ({len(pep_residues)} residues)",
        file=sys.stderr,
    )
    print(f"Target sequence: {target_sequence}", file=sys.stderr)

    # Apply mutations where sequences differ (use 3-letter codes)
    seq_to_use = target_sequence[:len(pep_residues)]
    n_mutations = 0
    for idx, pose_resnum in enumerate(pep_residues):
        if idx < len(seq_to_use) and ref_seq[idx] != seq_to_use[idx]:
            aa3 = _AA1TO3.get(seq_to_use[idx])
            if aa3 is None:
                print(f"  WARNING: Unknown AA '{seq_to_use[idx]}' at pos {idx}, skipping", file=sys.stderr)
                continue
            mutator = MutateResidue(pose_resnum, aa3)
            mutator.apply(pose)
            n_mutations += 1
            print(
                f"  Mutated pos {pose_resnum}: {ref_seq[idx]} -> {seq_to_use[idx]} ({aa3})",
                file=sys.stderr,
            )

    print(f"Applied {n_mutations} mutations", file=sys.stderr)
    return pose, resolved_chain


# ---------------------------------------------------------------------------
# Chain reordering (FlexPepDock expects peptide as LAST chain)
# ---------------------------------------------------------------------------

def reorder_peptide_last(
    pose: "pyrosetta.Pose", peptide_chain: int = 1,
) -> "pyrosetta.Pose":
    """Reorder pose so peptide chain is LAST (required by FlexPepDockingProtocol).

    Uses PDB text manipulation (most robust across PyRosetta versions):
    dump → reorder chain blocks → reload.
    """
    import pyrosetta
    import tempfile

    n_chains = pose.num_chains()
    if peptide_chain == n_chains:
        print(f"  Peptide already last chain ({peptide_chain}/{n_chains})", file=sys.stderr)
        return pose

    print(
        f"  Reordering: peptide chain {peptide_chain} → last (chain {n_chains})",
        file=sys.stderr,
    )

    # Dump current pose to PDB text
    tmp_orig = tempfile.mktemp(suffix=".pdb")
    pose.dump_pdb(tmp_orig)

    with open(tmp_orig) as fh:
        lines = fh.readlines()
    Path(tmp_orig).unlink(missing_ok=True)

    # Collect ATOM/HETATM/TER lines grouped by chain letter
    chain_blocks: dict[str, list[str]] = {}
    header_lines: list[str] = []
    chain_order: list[str] = []

    for line in lines:
        if line.startswith(("ATOM", "HETATM")):
            cid = line[21]
            if cid not in chain_blocks:
                chain_blocks[cid] = []
                chain_order.append(cid)
            chain_blocks[cid].append(line)
        elif line.startswith("TER"):
            pass  # We'll add TER between chains ourselves
        elif not line.startswith("END"):
            header_lines.append(line)

    if len(chain_order) < 2:
        print("  WARNING: Only 1 chain found, skipping reorder", file=sys.stderr)
        return pose

    # Peptide chain letter (0-indexed from chain_order)
    pep_letter = chain_order[peptide_chain - 1]

    # Build new order: non-peptide chains first, then peptide last
    new_order = [c for c in chain_order if c != pep_letter] + [pep_letter]

    # Reletter chains A, B, C, ... and write new PDB
    new_lines = header_lines[:]
    for idx, old_cid in enumerate(new_order):
        new_cid = chr(65 + idx)  # A, B, C, ...
        for atom_line in chain_blocks[old_cid]:
            new_lines.append(atom_line[:21] + new_cid + atom_line[22:])
        new_lines.append("TER\n")
    new_lines.append("END\n")

    tmp_reord = tempfile.mktemp(suffix="_reord.pdb")
    with open(tmp_reord, "w") as fh:
        fh.writelines(new_lines)

    new_pose = pyrosetta.pose_from_pdb(tmp_reord)
    Path(tmp_reord).unlink(missing_ok=True)

    print(
        f"  Reordered: {new_pose.num_chains()} chains, "
        f"{new_pose.total_residue()} residues "
        f"(chain order: {' → '.join(new_order)})",
        file=sys.stderr,
    )
    return new_pose


# ---------------------------------------------------------------------------
# Disulfide constraint helpers
# ---------------------------------------------------------------------------

def _find_peptide_cys_residues(pose: "pyrosetta.Pose") -> List[int]:
    """Find Cys residue numbers in the last chain (peptide after reordering)."""
    n_chains = pose.num_chains()
    cys_residues = []
    for i in range(1, pose.total_residue() + 1):
        if pose.chain(i) == n_chains and pose.residue(i).name1() == "C":
            cys_residues.append(i)
    return cys_residues


def _add_disulfide_constraint(
    pose: "pyrosetta.Pose",
    cys1_resnum: int,
    cys2_resnum: int,
) -> None:
    """Add SG-SG AtomPairConstraint for a disulfide bond (2.05 A, sd=0.3)."""
    from pyrosetta.rosetta.core.scoring.constraints import AtomPairConstraint
    from pyrosetta.rosetta.core.scoring.func import HarmonicFunc
    from pyrosetta.rosetta.core.id import AtomID

    sg1 = AtomID(pose.residue(cys1_resnum).atom_index("SG"), cys1_resnum)
    sg2 = AtomID(pose.residue(cys2_resnum).atom_index("SG"), cys2_resnum)
    func = HarmonicFunc(2.05, 0.3)
    constraint = AtomPairConstraint(sg1, sg2, func)
    pose.add_constraint(constraint)
    print(
        f"  [disulfide] Added SG-SG constraint: res {cys1_resnum} <-> res {cys2_resnum} "
        f"(harmonic 2.05 A, sd=0.3)",
        file=sys.stderr,
    )


def _check_disulfide_distance(
    pose: "pyrosetta.Pose",
    cys1_resnum: int,
    cys2_resnum: int,
) -> Tuple[bool, float]:
    """Check SG-SG distance after refinement. Returns (intact, distance)."""
    sg1_xyz = pose.residue(cys1_resnum).xyz("SG")
    sg2_xyz = pose.residue(cys2_resnum).xyz("SG")
    distance = sg1_xyz.distance(sg2_xyz)
    intact = distance < 3.0
    print(
        f"  [disulfide] Post-refinement SG-SG distance: {distance:.3f} A "
        f"({'INTACT' if intact else 'BROKEN'})",
        file=sys.stderr,
    )
    return intact, distance


# ---------------------------------------------------------------------------
# FlexPepDock protocols
# ---------------------------------------------------------------------------

def run_flexpep_refine_pose(
    pose: "pyrosetta.Pose", output_pdb: str
) -> Tuple["pyrosetta.Pose", Dict]:
    """Run FlexPepDock refinement on an existing Pose.

    Returns (refined_pose, disulfide_info) where disulfide_info may contain
    disulfide_intact and sg_sg_distance if exactly 2 Cys found in the peptide.
    """
    from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol

    disulfide_info: Dict = {}
    cys_residues = _find_peptide_cys_residues(pose)

    # Use PyRosetta built-in disulfide detection instead of manual AtomPairConstraint.
    # Manual constraint after PDB dump→reload chain reordering can corrupt AtomIDs
    # and cause segfaults in FlexPepDockingProtocol.apply().
    if len(cys_residues) == 2:
        try:
            pose.conformation().detect_disulfides()
            print(
                f"  [disulfide] Auto-detected disulfides via conformation().detect_disulfides()",
                file=sys.stderr,
            )
        except Exception as exc:
            print(
                f"  [disulfide] detect_disulfides() failed ({exc}), "
                f"falling back to manual constraint",
                file=sys.stderr,
            )
            try:
                _add_disulfide_constraint(pose, cys_residues[0], cys_residues[1])
            except Exception as exc2:
                print(
                    f"  [disulfide] Manual constraint also failed ({exc2}), "
                    f"proceeding without disulfide constraint",
                    file=sys.stderr,
                )

    fpd = FlexPepDockingProtocol()
    fpd.apply(pose)

    if len(cys_residues) == 2:
        intact, dist = _check_disulfide_distance(pose, cys_residues[0], cys_residues[1])
        disulfide_info["disulfide_intact"] = intact
        disulfide_info["sg_sg_distance"] = round(dist, 4)

    pose.dump_pdb(output_pdb)
    return pose, disulfide_info


def run_flexpep_refine(input_pdb: str, output_pdb: str) -> Tuple["pyrosetta.Pose", Dict]:
    """Run FlexPepDock refinement protocol on a receptor-peptide complex."""
    import pyrosetta

    pose = pyrosetta.pose_from_pdb(input_pdb)
    return run_flexpep_refine_pose(pose, output_pdb)


def run_flexpep_abinitio_pose(
    pose: "pyrosetta.Pose", output_pdb: str
) -> Tuple["pyrosetta.Pose", Dict]:
    """Run FlexPepDock ab-initio on an existing Pose.

    Returns (refined_pose, disulfide_info).
    """
    from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol

    disulfide_info: Dict = {}
    cys_residues = _find_peptide_cys_residues(pose)
    if len(cys_residues) == 2:
        _add_disulfide_constraint(pose, cys_residues[0], cys_residues[1])

    fpd = FlexPepDockingProtocol()
    fpd.set_lowres_preoptimize(True)
    fpd.apply(pose)

    if len(cys_residues) == 2:
        intact, dist = _check_disulfide_distance(pose, cys_residues[0], cys_residues[1])
        disulfide_info["disulfide_intact"] = intact
        disulfide_info["sg_sg_distance"] = round(dist, 4)

    pose.dump_pdb(output_pdb)
    return pose, disulfide_info


def run_flexpep_abinitio(input_pdb: str, output_pdb: str) -> Tuple["pyrosetta.Pose", Dict]:
    """Run FlexPepDock ab-initio protocol from PDB file."""
    import pyrosetta

    pose = pyrosetta.pose_from_pdb(input_pdb)
    return run_flexpep_abinitio_pose(pose, output_pdb)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_interface_ddg(pose: "pyrosetta.Pose") -> float:
    """Compute interface dG using InterfaceAnalyzerMover.

    Uses jump_id=1 to separate receptor (chain A) from peptide (chain B).
    Returns dG in kcal/mol (more negative = stronger binding).
    """
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover

    iam = InterfaceAnalyzerMover(1)
    iam.set_pack_input(True)
    iam.set_pack_separated(True)
    iam.apply(pose)
    return iam.get_interface_dG()


def compute_total_score(pose: "pyrosetta.Pose") -> float:
    """Compute total Rosetta energy score."""
    import pyrosetta
    scorefxn = pyrosetta.get_fa_scorefxn()
    return scorefxn(pose)


def compute_clash_score(pose: "pyrosetta.Pose") -> float:
    """Count PEPTIDE residues with high fa_rep (peptide-receptor steric clashes).

    Returns count of residues in the LAST chain (peptide — FlexPepDock reorders
    peptide last) where fa_rep > 10.0 REU.

    2026-06-09 fix: 이전 구현은 전체 pose(수용체+펩타이드, ~486 잔기)를 세어
    GPCR 수용체 내부 클래시까지 포함 → native·변이체 모두 clash~50 으로 QC
    게이트(<=10) 전원 탈락. 펩타이드 바인딩 QC 목적상 **펩타이드 체인 잔기만**
    세는 것이 옳다(펩타이드 잔기의 high fa_rep = 펩타이드-수용체 interface clash).
    """
    import pyrosetta
    from pyrosetta.rosetta.core.scoring import fa_rep

    scorefxn = pyrosetta.get_fa_scorefxn()
    scorefxn(pose)

    # 펩타이드 = 마지막 체인 (reorder_peptide_last 로 보장됨)
    n_chains = pose.num_chains()
    if n_chains >= 2:
        pep_begin = pose.chain_begin(n_chains)
        pep_end = pose.chain_end(n_chains)
    else:  # 단일 체인 폴백: 전체
        pep_begin, pep_end = 1, pose.total_residue()

    clash_count = 0
    for i in range(pep_begin, pep_end + 1):
        residue_energies = pose.energies().residue_total_energies(i)
        if residue_energies[fa_rep] > 10.0:
            clash_count += 1
    return float(clash_count)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PyRosetta FlexPepDock refinement + ddG calculation"
    )
    parser.add_argument("--input", required=True, help="Input complex PDB path")
    parser.add_argument("--output", required=True, help="Output refined PDB path")
    parser.add_argument(
        "--protocol",
        default="flexpep_refine",
        choices=["flexpep_refine", "flexpep_abinitio"],
        help="Docking protocol (default: flexpep_refine)",
    )
    parser.add_argument(
        "--reference-complex", default="",
        help="Reference complex PDB for MutateResidue approach (preferred)",
    )
    parser.add_argument(
        "--target-sequence", default="",
        help="Target peptide sequence for MutateResidue (used with --reference-complex)",
    )
    parser.add_argument(
        "--peptide-chain", type=int, default=1,
        help="Peptide chain number in reference complex (default: 1)",
    )
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(
            json.dumps({"error": f"Input PDB not found: {args.input}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Initialize PyRosetta (logs go to stderr via -mute all)
    init_pyrosetta()

    # Decide input mode: reference+mutation vs. direct PDB
    use_reference = (
        args.reference_complex
        and args.target_sequence
        and Path(args.reference_complex).exists()
    )

    disulfide_info: Dict = {}

    if use_reference:
        print(
            f"Mode: MutateResidue from reference complex",
            file=sys.stderr,
        )
        pose, resolved_chain = prepare_complex_by_mutation(
            args.reference_complex,
            args.target_sequence,
            args.peptide_chain,
        )
        # Reorder so peptide is LAST chain (FlexPepDock requirement)
        pose = reorder_peptide_last(pose, resolved_chain)

        # Score BEFORE refinement
        pre_score = compute_total_score(pose)
        print(f"Pre-refinement total_score: {pre_score:.2f}", file=sys.stderr)

        # Run FlexPepDock on the mutated pose
        if args.protocol == "flexpep_abinitio":
            pose, disulfide_info = run_flexpep_abinitio_pose(pose, args.output)
        else:
            pose, disulfide_info = run_flexpep_refine_pose(pose, args.output)
    else:
        # Direct PDB mode
        import pyrosetta as _pyr
        pose = _pyr.pose_from_pdb(args.input)
        # Reorder so peptide is LAST chain (FlexPepDock requirement)
        pose = reorder_peptide_last(pose, args.peptide_chain)
        pre_score = compute_total_score(pose)
        print(f"Pre-refinement total_score: {pre_score:.2f}", file=sys.stderr)

        if args.protocol == "flexpep_abinitio":
            pose, disulfide_info = run_flexpep_abinitio_pose(pose, args.output)
        else:
            pose, disulfide_info = run_flexpep_refine_pose(pose, args.output)

    # Score the refined pose
    total_score = compute_total_score(pose)
    ddg = compute_interface_ddg(pose)
    clash = compute_clash_score(pose)
    score_delta = total_score - pre_score

    print(f"Post-refinement total_score: {total_score:.2f} (delta={score_delta:.2f})", file=sys.stderr)

    result = {
        "ddg": round(ddg, 4),
        "total_score": round(total_score, 4),
        "pre_score": round(pre_score, 4),
        "score_delta": round(score_delta, 4),
        "clash_score": clash,
        "constraint_violations": 0,
    }
    if disulfide_info:
        result["disulfide_intact"] = disulfide_info["disulfide_intact"]
        result["sg_sg_distance"] = disulfide_info["sg_sg_distance"]

    # stdout = JSON only (parsed by step06_rosetta.py)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
