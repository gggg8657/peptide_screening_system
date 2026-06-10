#!/usr/bin/env bash
# =============================================================================
# download_models_offline.sh
# 집 PC (WSL/Linux)에서 모델 가중치 + whl 사전 다운로드
#
# 사용법:
#   bash download_models_offline.sh [다운로드_경로]
#   bash download_models_offline.sh /mnt/d/bio_models
#   bash download_models_offline.sh ~/bio_models
#
# 다운로드 후 USB/외장하드로 연구실 PC에 복사
# → 연구실에서 install_from_offline.sh 실행
# =============================================================================

set -euo pipefail

DEST="${1:-$HOME/bio_models}"
mkdir -p "$DEST"
cd "$DEST"

echo "=============================================="
echo " 오프라인 설치용 다운로드"
echo " 저장 경로: $DEST"
echo " 예상 총량: ~20 GB"
echo "=============================================="

# ---------------------------------------------------------------------------
# 1. PyTorch whl 파일
# ---------------------------------------------------------------------------
echo ""
echo "[1/5] PyTorch whl 다운로드..."

# bio-tools용 (cu124)
mkdir -p wheels/cu124
pip download torch torchvision \
    --index-url https://download.pytorch.org/whl/cu124 \
    --dest wheels/cu124/ \
    --python-version 3.12 --only-binary=:all: --platform manylinux2014_x86_64 \
    2>&1 | tail -5
echo "  cu124 완료: $(du -sh wheels/cu124/ | cut -f1)"

# rfdiffusion용 (cu117, python 3.9)
mkdir -p wheels/cu117
pip download torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1 \
    --index-url https://download.pytorch.org/whl/cu117 \
    --dest wheels/cu117/ \
    --python-version 3.9 --only-binary=:all: --platform manylinux2014_x86_64 \
    2>&1 | tail -5
echo "  cu117 완료: $(du -sh wheels/cu117/ | cut -f1)"

# ---------------------------------------------------------------------------
# 2. ESMFold 가중치 (~2.5 GB)
# ---------------------------------------------------------------------------
echo ""
echo "[2/5] ESMFold 가중치 다운로드..."
mkdir -p esmfold
cd esmfold

# HuggingFace에서 직접 다운로드
pip install -q huggingface_hub 2>/dev/null || true
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('facebook/esmfold_v1', local_dir='./esmfold_v1', local_dir_use_symlinks=False)
print('ESMFold 다운로드 완료')
" 2>&1 | tail -3

cd "$DEST"
echo "  ESMFold: $(du -sh esmfold/ | cut -f1)"

# ---------------------------------------------------------------------------
# 3. RFdiffusion 가중치 (~10 GB) + 소스
# ---------------------------------------------------------------------------
echo ""
echo "[3/5] RFdiffusion 다운로드..."
mkdir -p rfdiffusion/models

# git clone
if [ -d "rfdiffusion/repo" ]; then
    echo "  repo 이미 존재 — skip"
else
    git clone --depth 1 https://github.com/RosettaCommons/RFdiffusion.git rfdiffusion/repo
fi

# 모델 가중치
WEIGHTS=(
    "6f5902ac237024bdd0c176cb93063dc4/Base_ckpt.pt"
    "e29311f6f1bf1af907f9ef9f44b8328b/Complex_base_ckpt.pt"
    "60f09a193fb5e5ccdc4980417708dbab/Complex_Fold_base_ckpt.pt"
    "74f51cfb8b440f50d70878e05361d8f0/InpaintSeq_ckpt.pt"
    "76d00716416567174cdb7ca96e208296/InpaintSeq_Fold_ckpt.pt"
    "5532d2e1f3a4738decd58b19d633b3c3/ActiveSite_ckpt.pt"
    "12fc204edeae5b57713c5ad7dcb97d39/Base_epoch8_ckpt.pt"
    "f572d396fae9206628714fb2ce00f72e/Complex_beta_ckpt.pt"
)
for w in "${WEIGHTS[@]}"; do
    fname=$(basename "$w")
    if [ -f "rfdiffusion/models/$fname" ]; then
        echo "  $fname 이미 존재 — skip"
    else
        echo "  다운로드: $fname"
        wget -q --show-progress "http://files.ipd.uw.edu/pub/RFdiffusion/$w" \
            -O "rfdiffusion/models/$fname"
    fi
done
echo "  RFdiffusion: $(du -sh rfdiffusion/ | cut -f1)"

# ---------------------------------------------------------------------------
# 4. DiffPepDock 가중치 + 소스
# ---------------------------------------------------------------------------
echo ""
echo "[4/5] DiffPepDock 다운로드..."
mkdir -p diffpepdock

if [ -d "diffpepdock/repo" ]; then
    echo "  repo 이미 존재 — skip"
else
    git clone --depth 1 https://github.com/YuzheWangPKU/DiffPepBuilder.git diffpepdock/repo
fi

if [ -f "diffpepdock/diffpepdock_v1.pth" ]; then
    echo "  가중치 이미 존재 — skip"
else
    wget -q --show-progress \
        "https://zenodo.org/records/15398020/files/diffpepdock_v1.pth" \
        -O diffpepdock/diffpepdock_v1.pth
fi
echo "  DiffPepDock: $(du -sh diffpepdock/ | cut -f1)"

# ---------------------------------------------------------------------------
# 5. LigandMPNN + transformers whl
# ---------------------------------------------------------------------------
echo ""
echo "[5/5] 추가 pip 패키지 다운로드..."
mkdir -p wheels/pip_extra
pip download ligandmpnn transformers accelerate biotite \
    --dest wheels/pip_extra/ \
    --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.12 \
    2>&1 | tail -5 || echo "  일부 패키지 소스 빌드 필요할 수 있음"
echo "  pip_extra: $(du -sh wheels/pip_extra/ | cut -f1)"

# ---------------------------------------------------------------------------
# 완료
# ---------------------------------------------------------------------------
echo ""
echo "=============================================="
echo " 다운로드 완료!"
echo ""
echo " 총 크기: $(du -sh "$DEST" | cut -f1)"
echo ""
echo " 디렉토리 구조:"
echo "   $DEST/"
echo "   ├── wheels/cu124/      (PyTorch + CUDA 12.4)"
echo "   ├── wheels/cu117/      (PyTorch 1.13.1 + CUDA 11.7)"
echo "   ├── wheels/pip_extra/  (transformers, ligandmpnn 등)"
echo "   ├── esmfold/           (ESMFold 가중치)"
echo "   ├── rfdiffusion/       (소스 + 모델 가중치 8개)"
echo "   └── diffpepdock/       (소스 + 모델 가중치)"
echo ""
echo " 다음 단계:"
echo "   1. 이 폴더를 USB/외장하드에 복사"
echo "   2. 연구실 PC에서: bash install_from_offline.sh /path/to/bio_models"
echo "=============================================="
