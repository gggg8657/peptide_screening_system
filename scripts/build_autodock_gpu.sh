#!/usr/bin/env bash
# Build AutoDock-GPU (CUDA or OpenCL). Run from repo root or set ADGPU_SRC.
# Prereqs: CUDA toolkit (for GPU) or OpenCL headers. See docs/ENV_COMPATIBILITY.md.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ADGPU_SRC="${ADGPU_SRC:-$REPO_ROOT/tools/AutoDock-GPU}"

if [[ ! -d "$ADGPU_SRC" ]]; then
  echo "AutoDock-GPU source not found at $ADGPU_SRC"
  echo "Clone with: git clone https://github.com/ccsb-scripps/AutoDock-GPU.git $ADGPU_SRC && cd $ADGPU_SRC && git submodule update --init --recursive"
  exit 1
fi

# Prefer CUDA if available
if [[ -d /usr/local/cuda ]]; then
  export GPU_INCLUDE_PATH="/usr/local/cuda/include"
  export GPU_LIBRARY_PATH="/usr/local/cuda/lib64"
elif [[ -f /usr/include/cuda.h ]]; then
  export GPU_INCLUDE_PATH="/usr/include"
  export GPU_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu"
else
  echo "CUDA headers not found. Install CUDA toolkit or: sudo apt install nvidia-cuda-dev"
  echo "Then set GPU_INCLUDE_PATH and GPU_LIBRARY_PATH (see https://github.com/ccsb-scripps/AutoDock-GPU/wiki/Guideline-for-users)"
  exit 1
fi

cd "$ADGPU_SRC"
# NUMWI=64 or 128 typical for modern GPUs
make DEVICE=GPU NUMWI=64
echo "Build done. Binary: $ADGPU_SRC/bin/autodock_gpu_64wi"
echo "Add to PATH or use: export PATH=\"$ADGPU_SRC/bin:\$PATH\""
