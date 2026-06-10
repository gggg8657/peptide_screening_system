#!/usr/bin/env bash
# =============================================================================
# setup_ubuntu2204.sh
# One-click setup for bio-tools conda environment on Ubuntu 22.04 / WSL2
# Includes: PyRosetta, FoldMason, PyMOL, Biopython, Meeko
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$REPO_ROOT/environment-bio-tools.yml"
ENV_NAME="bio-tools"

echo "=============================================="
echo " Bio-tools Environment Setup (Ubuntu 22.04)"
echo "=============================================="

# -----------------------------------------------------------------------------
# 1. Check/Install Miniconda
# -----------------------------------------------------------------------------
if command -v conda &> /dev/null; then
    echo "[OK] Conda already installed: $(conda --version)"
else
    echo "[INFO] Conda not found. Installing Miniconda..."
    INSTALLER="Miniconda3-latest-Linux-x86_64.sh"
    wget -q "https://repo.anaconda.com/miniconda/${INSTALLER}" -O "/tmp/${INSTALLER}"
    bash "/tmp/${INSTALLER}" -b -p "$HOME/miniconda3"
    rm -f "/tmp/${INSTALLER}"
    
    # Initialize conda for current shell
    eval "$("$HOME/miniconda3/bin/conda" shell.bash hook)"
    "$HOME/miniconda3/bin/conda" init bash
    echo "[OK] Miniconda installed to $HOME/miniconda3"
fi

# Ensure conda is available in current session
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "/opt/conda/etc/profile.d/conda.sh" ]]; then
    source "/opt/conda/etc/profile.d/conda.sh"
fi

# -----------------------------------------------------------------------------
# 2. Create/Update conda environment
# -----------------------------------------------------------------------------
echo ""
echo "[INFO] Creating conda environment from: $ENV_FILE"

if conda env list | grep -q "^${ENV_NAME} "; then
    echo "[INFO] Environment '$ENV_NAME' exists. Updating..."
    conda env update -n "$ENV_NAME" -f "$ENV_FILE" --prune
else
    echo "[INFO] Creating new environment '$ENV_NAME'..."
    conda env create -f "$ENV_FILE"
fi

echo "[OK] Environment '$ENV_NAME' ready."

# -----------------------------------------------------------------------------
# 3. Verify installation
# -----------------------------------------------------------------------------
echo ""
echo "[INFO] Verifying installed packages..."
conda activate "$ENV_NAME"

VERIFY_SCRIPT="$REPO_ROOT/scripts/verify_bio_tools_env.py"
if [[ -f "$VERIFY_SCRIPT" ]]; then
    python "$VERIFY_SCRIPT"
else
    # Quick inline verification
    python -c "
import sys
packages = {
    'Bio': 'biopython',
    'rdkit': 'rdkit', 
    'gemmi': 'gemmi',
    'numpy': 'numpy',
    'scipy': 'scipy',
}
failed = []
for mod, name in packages.items():
    try:
        __import__(mod)
        print(f'  [OK] {name}')
    except ImportError:
        print(f'  [FAIL] {name}')
        failed.append(name)

# Check CLI tools
import subprocess
for tool in ['foldmason', 'pymol']:
    try:
        subprocess.run([tool, '--version'], capture_output=True, timeout=5)
        print(f'  [OK] {tool} (CLI)')
    except Exception:
        print(f'  [FAIL] {tool} (CLI)')
        failed.append(tool)

# PyRosetta check
try:
    import pyrosetta
    print('  [OK] pyrosetta')
except ImportError:
    print('  [FAIL] pyrosetta')
    failed.append('pyrosetta')

if failed:
    print(f'\\n[WARN] Some packages failed: {failed}')
    sys.exit(1)
else:
    print('\\n[OK] All packages verified successfully!')
"
fi

# -----------------------------------------------------------------------------
# 4. Done
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo " Setup complete!"
echo " Activate with: conda activate $ENV_NAME"
echo "=============================================="
