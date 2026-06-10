#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true
cd "$REPO_ROOT"

echo "=== Git status ==="
git status --short

echo ""
echo "=== Add new files ==="
# API clients
git add bionemo/api_base.py
git add bionemo/diffdock_client.py
git add bionemo/rfdiffusion_client.py
git add bionemo/proteinmpnn_client.py
git add bionemo/esmfold_client.py

# Pipeline scripts
git add bionemo/04_sstr2_pocket_analysis.py
git add bionemo/05_sstr2_smallmol_screen.py
git add bionemo/06_sstr2_flexpep_dock.py
git add bionemo/07_sstr2_denovo_binder.py

# Results (pocket + docking structure data)
git add results/sstr2_docking/binding_pocket.json
git add results/sstr2_docking/sstr2_receptor.pdb

# Experiment doc
git add experiments/05_sstr2_virtual_screening.md

# Runner scripts
git add scripts/run_sstr2_pipeline.sh
git add scripts/run_arm1.sh
git add scripts/run_arm2.sh
git add scripts/run_arm3.sh

# Updated .gitignore
git add .gitignore

echo ""
echo "=== Staged files ==="
git diff --cached --stat

echo ""
echo "=== Commit ==="
git commit -m "feat: SSTR2 virtual screening pipeline (3-arm approach)

- Step 0: Binding pocket analysis (35 contact residues identified)
- Arm 1: Small molecule screening (MolMIM + DiffDock, 15/15 docked)
- Arm 2: Somatostatin variant analysis (13 variants, FlexPepDock pending)
- Arm 3: De novo peptide binder design (RFdiffusion + ProteinMPNN + ESMFold)
  - 4 novel backbones, 16 designed sequences, all ESMFold verified
  - Top binder: AALARTIAARFRKELEA (pLDDT=81.4)
- 5 NVIDIA NIM API clients (MolMIM, DiffDock, RFdiffusion, ProteinMPNN, ESMFold)
- Common API base class (api_base.py)
- Experiment documentation (experiments/05_sstr2_virtual_screening.md)"

echo ""
echo "=== Push to prst ==="
git push prst main 2>&1

echo ""
echo "=== Final log ==="
git log --oneline -3
