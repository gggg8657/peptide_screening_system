#!/usr/bin/env bash
# =============================================================================
# install_from_offline.sh
# 오프라인 다운로드 데이터로부터 연구실 PC에 설치
#
# 사전 조건:
#   - download_models_offline.sh로 다운로드한 폴더를 USB로 복사
#   - conda 설치 완료
#
# 사용법:
#   bash install_from_offline.sh /media/usb/bio_models
#   bash install_from_offline.sh /mnt/external/bio_models
# =============================================================================

set -euo pipefail

SRC="${1:?사용법: bash install_from_offline.sh /path/to/bio_models}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$PROJECT_DIR/local_models"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'
log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# conda 초기화
if [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniforge3/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
else
    eval "$(conda shell.bash hook 2>/dev/null)"
fi

echo "=============================================="
echo " 오프라인 설치"
echo " 소스: $SRC"
echo " 대상: $PROJECT_DIR"
echo "=============================================="

# =============================================
# 1. bio-tools: PyTorch + ESMFold + ProteinMPNN
# =============================================
log_info "===== bio-tools env 설치 ====="
conda activate bio-tools

# PyTorch (오프라인)
log_info "PyTorch 오프라인 설치 (cu124)..."
pip install --no-index --find-links="$SRC/wheels/cu124/" torch torchvision 2>&1 | tail -3

# transformers, ligandmpnn 등
log_info "transformers + ligandmpnn 설치..."
pip install --no-index --find-links="$SRC/wheels/pip_extra/" \
    transformers accelerate biotite ligandmpnn 2>&1 | tail -3 \
    || pip install transformers accelerate biotite ligandmpnn 2>&1 | tail -3

# ESMFold 가중치 복사
log_info "ESMFold 가중치 복사..."
HF_CACHE="$HOME/.cache/huggingface/hub/models--facebook--esmfold_v1"
mkdir -p "$HF_CACHE"
if [ -d "$SRC/esmfold/esmfold_v1" ]; then
    cp -r "$SRC/esmfold/esmfold_v1/"* "$HF_CACHE/" 2>/dev/null || \
    rsync -a "$SRC/esmfold/esmfold_v1/" "$HF_CACHE/"
    log_ok "ESMFold 가중치 복사 완료"
fi

# 검증
log_info "bio-tools 검증..."
python -c "
import torch
print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')
from transformers import EsmForProteinFolding
print('ESMFold import OK')
" 2>&1
log_ok "bio-tools 완료"

# =============================================
# 2. rfdiffusion env
# =============================================
log_info "===== rfdiffusion env 설치 ====="

if ! conda env list | grep -q "rfdiffusion"; then
    conda create -n rfdiffusion python=3.9 -y 2>&1 | tail -3
fi
conda activate rfdiffusion

# PyTorch 1.13.1 (오프라인)
log_info "PyTorch 1.13.1 오프라인 설치 (cu117)..."
pip install --no-index --find-links="$SRC/wheels/cu117/" \
    torch torchvision torchaudio 2>&1 | tail -3 \
    || conda install pytorch=1.13.1 torchvision torchaudio pytorch-cuda=11.7 \
        -c pytorch -c nvidia -y 2>&1 | tail -3

# DGL
conda install -c dglteam dgl-cuda11.7 -y 2>&1 | tail -3

# RFdiffusion 소스 복사 + 설치
mkdir -p "$MODELS_DIR"
log_info "RFdiffusion 소스 복사..."
if [ -d "$SRC/rfdiffusion/repo" ]; then
    cp -r "$SRC/rfdiffusion/repo" "$MODELS_DIR/RFdiffusion" 2>/dev/null || \
    rsync -a "$SRC/rfdiffusion/repo/" "$MODELS_DIR/RFdiffusion/"
fi
cd "$MODELS_DIR/RFdiffusion"

pip install hydra-core pyrsistent "numpy<2.0" 2>&1 | tail -3
cd env/SE3Transformer
pip install --no-cache-dir -r requirements.txt 2>&1 | tail -3
python setup.py install 2>&1 | tail -3
cd "$MODELS_DIR/RFdiffusion"
pip install -e . 2>&1 | tail -3

# 가중치 복사
log_info "RFdiffusion 가중치 복사..."
mkdir -p models
cp "$SRC/rfdiffusion/models/"*.pt models/
log_ok "rfdiffusion 완료"

# =============================================
# 3. diffpepdock env
# =============================================
log_info "===== diffpepdock env 설치 ====="

if [ -d "$SRC/diffpepdock/repo" ]; then
    cp -r "$SRC/diffpepdock/repo" "$MODELS_DIR/DiffPepBuilder" 2>/dev/null || \
    rsync -a "$SRC/diffpepdock/repo/" "$MODELS_DIR/DiffPepBuilder/"
fi
cd "$MODELS_DIR/DiffPepBuilder"

if [ -f "environment.yml" ]; then
    if ! conda env list | grep -q "diffpepdock"; then
        conda env create -f environment.yml 2>&1 | tail -5
    fi
fi
conda activate diffpepdock 2>/dev/null || conda activate diffpepbuilder

# 가중치 복사
mkdir -p experiments/checkpoints
cp "$SRC/diffpepdock/diffpepdock_v1.pth" experiments/checkpoints/
log_ok "diffpepdock 완료"

# =============================================
# 완료
# =============================================
cd "$PROJECT_DIR"
echo ""
echo "=============================================="
log_ok "전체 오프라인 설치 완료!"
echo ""
echo "  conda activate bio-tools     → ESMFold + ProteinMPNN"
echo "  conda activate rfdiffusion   → RFdiffusion"
echo "  conda activate diffpepdock   → DiffPepDock"
echo "=============================================="
