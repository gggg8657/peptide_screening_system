#!/usr/bin/env bash
# Open PyMOL with PDB file(s). Usage: ./scripts/run_pymol_pdb.sh [file.pdb ...]
# Default: fold_test1_model_0.pdb in "fold_test1 (1)"
set -e
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_pdb="${REPO}/data/fold_test1/fold_test1_model_0.pdb"
files=("${@:-$default_pdb}")

conda run -n bio-tools pymol "${files[@]}"
