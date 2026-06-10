#!/usr/bin/env python3
"""Lightweight PDB receptor structure diagnostics.

Reports chain/residue composition, REMARK 465 missing residues, non-standard
residues, high B-factors, and simple heavy-atom clashes without modifying input.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

STANDARD_AA = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}


def _iter_pdb_atoms(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", errors="replace") as handle:
        for line in handle:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            if len(line) < 66:
                continue
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                occ = float(line[54:60])
                bfactor = float(line[60:66])
            except ValueError:
                continue
            yield {
                "record": line[:6].strip(),
                "serial": int(line[6:11]),
                "atom": line[12:16].strip(),
                "resname": line[17:20].strip(),
                "chain": line[21].strip() or "_",
                "resseq": line[22:26].strip(),
                "icode": line[26].strip(),
                "x": x,
                "y": y,
                "z": z,
                "occupancy": occ,
                "bfactor": bfactor,
                "element": line[76:78].strip(),
            }


def _parse_remark_465(path: Path) -> List[str]:
    missing = []
    with path.open("r", errors="replace") as handle:
        for line in handle:
            if line.startswith("REMARK 465"):
                missing.append(line.rstrip())
    return missing


def _find_clashes(atoms: List[Dict[str, Any]], cutoff: float) -> List[Dict[str, Any]]:
    heavy = [a for a in atoms if a["element"].upper() != "H" and not a["atom"].startswith("H")]
    clashes = []
    for i, atom_a in enumerate(heavy):
        for atom_b in heavy[i + 1:]:
            if atom_a["chain"] == atom_b["chain"] and atom_a["resseq"] == atom_b["resseq"]:
                continue
            dx = atom_a["x"] - atom_b["x"]
            dy = atom_a["y"] - atom_b["y"]
            dz = atom_a["z"] - atom_b["z"]
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)
            if distance < cutoff:
                clashes.append(
                    {
                        "distance": round(distance, 3),
                        "atom1": _atom_label(atom_a),
                        "atom2": _atom_label(atom_b),
                    }
                )
    return sorted(clashes, key=lambda item: item["distance"])


def _atom_label(atom: Dict[str, Any]) -> str:
    return f"{atom['chain']}:{atom['resname']}{atom['resseq']}:{atom['atom']}#{atom['serial']}"


def inspect_pdb(path: Path, bfactor_threshold: float, clash_cutoff: float) -> Dict[str, Any]:
    atoms = list(_iter_pdb_atoms(path))
    chain_residues: Dict[str, set] = defaultdict(set)
    residue_counts: Counter[str] = Counter()
    nonstandard: Counter[str] = Counter()
    high_bfactor = []

    for atom in atoms:
        residue_key = (atom["resname"], atom["resseq"], atom["icode"])
        chain_residues[atom["chain"]].add(residue_key)
        residue_counts[f"{atom['chain']}:{atom['resname']}"] += 1
        if atom["record"] == "ATOM" and atom["resname"] not in STANDARD_AA:
            nonstandard[f"{atom['chain']}:{atom['resname']}"] += 1
        if atom["bfactor"] > bfactor_threshold:
            high_bfactor.append(
                {
                    "atom": _atom_label(atom),
                    "bfactor": atom["bfactor"],
                }
            )

    clashes = _find_clashes(atoms, clash_cutoff)
    return {
        "path": str(path),
        "atom_count": len(atoms),
        "chains": {
            chain: len(residues)
            for chain, residues in sorted(chain_residues.items())
        },
        "residue_atom_counts": dict(sorted(residue_counts.items())),
        "remark_465_count": len(_parse_remark_465(path)),
        "remark_465_head": _parse_remark_465(path)[:20],
        "nonstandard_atom_residues": dict(sorted(nonstandard.items())),
        "high_bfactor_count": len(high_bfactor),
        "high_bfactor_head": high_bfactor[:20],
        "clash_cutoff_angstrom": clash_cutoff,
        "clash_count": len(clashes),
        "clash_head": clashes[:20],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect PDB receptor preprocessing issues.")
    parser.add_argument("pdb", type=Path)
    parser.add_argument("--bfactor-threshold", type=float, default=100.0)
    parser.add_argument("--clash-cutoff", type=float, default=0.8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = inspect_pdb(args.pdb, args.bfactor_threshold, args.clash_cutoff)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
