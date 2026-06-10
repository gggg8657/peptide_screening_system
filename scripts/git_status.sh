#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate bio-tools 2>/dev/null || true

cd "$REPO_ROOT"
echo "=== git remote ==="
git remote -v

echo ""
echo "=== git status ==="
git status

echo ""
echo "=== git log (last 3) ==="
git log --oneline -3

echo ""
echo "=== untracked/new files ==="
git status --short
