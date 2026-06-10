#!/usr/bin/env python3
"""
Convert mmCIF files in fold_test1 folder to PDB using Biopython.
Usage: python scripts/cif_to_pdb.py [input_dir] [output_dir]
  Default: input_dir = "fold_test1 (1)", output_dir = same as input (writes .pdb alongside .cif)
"""
import sys
import os
from pathlib import Path

from Bio.PDB import MMCIFParser, PDBIO


def convert_cif_to_pdb(cif_path: Path, pdb_path: Path, quiet: bool = True) -> bool:
    """Convert a single mmCIF file to PDB. Returns True on success."""
    parser = MMCIFParser(QUIET=quiet)
    try:
        structure = parser.get_structure("structure", str(cif_path))
    except Exception as e:
        print(f"  Parse error {cif_path.name}: {e}", file=sys.stderr)
        return False
    io_handler = PDBIO()
    io_handler.set_structure(structure)
    try:
        io_handler.save(str(pdb_path))
    except Exception as e:
        print(f"  Write error {pdb_path.name}: {e}", file=sys.stderr)
        return False
    return True


def main():
    repo_root = Path(__file__).resolve().parents[1]
    if len(sys.argv) >= 2:
        input_dir = Path(sys.argv[1])
    else:
        input_dir = repo_root / "data" / "fold_test1"
    if len(sys.argv) >= 3:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = input_dir  # same dir as input

    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all .cif under input_dir (root + subdirs like templates/)
    cif_files = list(input_dir.rglob("*.cif"))
    if not cif_files:
        print(f"No .cif files in {input_dir}", file=sys.stderr)
        sys.exit(1)

    ok = 0
    for cif_path in sorted(cif_files):
        rel = cif_path.relative_to(input_dir)
        pdb_path = output_dir / rel.with_suffix(".pdb")
        pdb_path.parent.mkdir(parents=True, exist_ok=True)
        if convert_cif_to_pdb(cif_path, pdb_path):
            ok += 1
            print(f"  {rel} -> {pdb_path.relative_to(output_dir)}")
        else:
            print(f"  SKIP {rel}")

    print(f"Done: {ok}/{len(cif_files)} converted.")
    sys.exit(0 if ok == len(cif_files) else 1)


if __name__ == "__main__":
    main()
