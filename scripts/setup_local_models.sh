#!/usr/bin/env bash
# =============================================================================
# setup_local_models.sh
# NIM Cloud API → 로컬 모델 전환 설치 스크립트
#
# 대상 모델:
#   1. ESMFold      (bio-tools env) — 구조 예측
#   2. ProteinMPNN  (bio-tools env) — 역폴딩 (백본→시퀀스)
#   3. RFdiffusion  (rfdiffusion env) — 백본 생성
#   4. DiffPepDock  (diffpepdock env) — 펩타이드-단백질 도킹
#
# GPU 요구사항: RTX 4090 24GB (또는 동급 이상)
# 총 디스크: ~25GB (모델 가중치 포함)
# 총 설치 시간: ~30-40분 (네트워크 속도 의존)
#
# 사용법:
#   chmod +x scripts/setup_local_models.sh
#   ./scripts/setup_local_models.sh [all|esmfold|proteinmpnn|rfdiffusion|diffpepdock]
#   (인자 없으면 all)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_ROOT/local_models"
LOG_DIR="$PROJECT_ROOT/logs/setup"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }

mkdir -p "$MODELS_DIR" "$LOG_DIR"

# ---------------------------------------------------------------------------
# conda 초기화
# ---------------------------------------------------------------------------
init_conda() {
    if [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniforge3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    else
        eval "$(conda shell.bash hook 2>/dev/null)" || {
            log_err "conda를 찾을 수 없습니다. conda를 먼저 설치하세요."
            exit 1
        }
    fi
}

# ---------------------------------------------------------------------------
# GPU 확인
# ---------------------------------------------------------------------------
check_gpu() {
    log_info "GPU 확인 중..."
    if ! command -v nvidia-smi &>/dev/null; then
        log_err "nvidia-smi를 찾을 수 없습니다. NVIDIA 드라이버를 설치하세요."
        exit 1
    fi
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    log_ok "GPU 확인 완료"
}

# =============================================================================
# 1. ESMFold (bio-tools env)
# =============================================================================
setup_esmfold() {
    log_info "========== ESMFold 설치 시작 =========="
    conda activate bio-tools

    # PyTorch (이미 설치되어 있으면 skip)
    if python -c "import torch; print(torch.__version__)" 2>/dev/null; then
        log_ok "PyTorch 이미 설치됨: $(python -c 'import torch; print(torch.__version__)')"
    else
        log_info "PyTorch 설치 중 (cu124)..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124 \
            2>&1 | tee "$LOG_DIR/pytorch_install.log" | tail -3
    fi

    # transformers + accelerate (ESMFold용)
    log_info "transformers + accelerate 설치 중..."
    pip install transformers accelerate biotite 2>&1 | tail -3

    # ProteinMPNN도 같은 env
    log_info "LigandMPNN (ProteinMPNN 포함) 설치 중..."
    pip install ligandmpnn 2>&1 | tail -3

    # ESMFold 모델 가중치 사전 다운로드 (~2.5GB)
    log_info "ESMFold 가중치 사전 다운로드 중 (facebook/esmfold_v1)..."
    python -c "
from transformers import AutoTokenizer, EsmForProteinFolding
print('Downloading ESMFold model weights...')
tokenizer = AutoTokenizer.from_pretrained('facebook/esmfold_v1')
model = EsmForProteinFolding.from_pretrained('facebook/esmfold_v1', low_cpu_mem_usage=True)
print('ESMFold weights cached successfully.')
" 2>&1 | tee "$LOG_DIR/esmfold_download.log" | tail -5

    # 검증
    log_info "ESMFold 검증 중..."
    python -c "
import torch
from transformers import AutoTokenizer, EsmForProteinFolding
tokenizer = AutoTokenizer.from_pretrained('facebook/esmfold_v1')
model = EsmForProteinFolding.from_pretrained('facebook/esmfold_v1', low_cpu_mem_usage=True)
model = model.cuda().half().eval()
seq = 'AGCKNFFWKTFTSC'
with torch.no_grad():
    tok = tokenizer([seq], return_tensors='pt', add_special_tokens=False)
    tok = {k: v.cuda() for k, v in tok.items()}
    out = model(**tok)
plddt = out.plddt[0, 1:len(seq)+1].mean().item()
print(f'ESMFold OK — SST-14 mean pLDDT: {plddt:.1f}')
" 2>&1 | tee "$LOG_DIR/esmfold_verify.log"

    log_ok "ESMFold + ProteinMPNN 설치 완료"
}

# =============================================================================
# 2. ProteinMPNN (bio-tools env — ESMFold와 함께 설치됨)
# =============================================================================
setup_proteinmpnn() {
    log_info "========== ProteinMPNN 설치 시작 =========="
    conda activate bio-tools

    if python -c "import ligandmpnn" 2>/dev/null; then
        log_ok "LigandMPNN 이미 설치됨"
    else
        pip install ligandmpnn 2>&1 | tail -3
    fi

    # 검증 (CLI)
    log_info "ProteinMPNN 검증 중..."
    if command -v ligandmpnn &>/dev/null; then
        ligandmpnn --help 2>&1 | head -3
        log_ok "ProteinMPNN (LigandMPNN) 설치 완료"
    else
        log_warn "ligandmpnn CLI를 찾을 수 없음 — Python import로 확인"
        python -c "from ligandmpnn import run; print('LigandMPNN import OK')"
    fi
}

# =============================================================================
# 3. RFdiffusion (별도 env — Python 3.9 + PyTorch 1.13.1 필수)
# =============================================================================
setup_rfdiffusion() {
    log_info "========== RFdiffusion 설치 시작 =========="

    RFDIFF_DIR="$MODELS_DIR/RFdiffusion"

    # conda env 생성
    if conda env list | grep -q "rfdiffusion"; then
        log_warn "rfdiffusion env 이미 존재 — 기존 env 사용"
    else
        log_info "rfdiffusion conda env 생성 중 (Python 3.9)..."
        conda create -n rfdiffusion python=3.9 -y 2>&1 | tail -3
    fi
    conda activate rfdiffusion

    # PyTorch 1.13.1 + CUDA 11.7 (RTX 4090 호환 검증됨)
    if python -c "import torch; print(torch.__version__)" 2>/dev/null; then
        log_ok "PyTorch 이미 설치됨"
    else
        log_info "PyTorch 1.13.1 + CUDA 11.7 설치 중..."
        conda install pytorch=1.13.1 torchvision torchaudio pytorch-cuda=11.7 \
            -c pytorch -c nvidia -y 2>&1 | tee "$LOG_DIR/rfdiff_pytorch.log" | tail -3
    fi

    # DGL
    log_info "DGL 설치 중..."
    conda install -c dglteam dgl-cuda11.7 -y 2>&1 | tail -3

    # Clone RFdiffusion
    if [ -d "$RFDIFF_DIR" ]; then
        log_warn "RFdiffusion 디렉토리 이미 존재 — git pull"
        cd "$RFDIFF_DIR" && git pull 2>/dev/null || true
    else
        log_info "RFdiffusion 클론 중..."
        git clone https://github.com/RosettaCommons/RFdiffusion.git "$RFDIFF_DIR"
    fi
    cd "$RFDIFF_DIR"

    # SE3-Transformer 빌드
    log_info "SE3-Transformer 빌드 중..."
    pip install hydra-core pyrsistent "numpy<2.0" 2>&1 | tail -3
    cd env/SE3Transformer
    pip install --no-cache-dir -r requirements.txt 2>&1 | tail -3
    python setup.py install 2>&1 | tail -3
    cd "$RFDIFF_DIR"

    # RFdiffusion 설치
    pip install -e . 2>&1 | tail -3

    # 모델 가중치 다운로드 (~10GB)
    log_info "RFdiffusion 모델 가중치 다운로드 중 (~10GB)..."
    mkdir -p models
    cd models

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
        if [ -f "$fname" ]; then
            log_ok "$fname 이미 존재 — skip"
        else
            wget -q --show-progress "http://files.ipd.uw.edu/pub/RFdiffusion/$w" -O "$fname"
        fi
    done

    cd "$RFDIFF_DIR"
    log_info "RFdiffusion 검증 중..."
    python -c "
from rfdiffusion.inference.model_runners import InferenceModel
print('RFdiffusion import OK')
" 2>&1 || log_warn "RFdiffusion import 실패 — SE3-Transformer 빌드 확인 필요"

    log_ok "RFdiffusion 설치 완료"
}

# =============================================================================
# 4. DiffPepDock (별도 env — 펩타이드-단백질 도킹 전용)
#    DiffDock(소분자 전용)이 아닌 DiffPepDock(펩타이드 전용) 사용
# =============================================================================
setup_diffpepdock() {
    log_info "========== DiffPepDock 설치 시작 =========="

    DPPD_DIR="$MODELS_DIR/DiffPepBuilder"

    # conda env 생성
    if conda env list | grep -q "diffpepdock"; then
        log_warn "diffpepdock env 이미 존재 — 기존 env 사용"
    else
        log_info "diffpepdock conda env 생성 중..."
        # DiffPepBuilder의 environment.yml 사용
        if [ -f "$DPPD_DIR/environment.yml" ]; then
            conda env create -f "$DPPD_DIR/environment.yml" 2>&1 | tail -5
        else
            # 먼저 clone 후 env 생성
            git clone https://github.com/YuzheWangPKU/DiffPepBuilder.git "$DPPD_DIR"
            cd "$DPPD_DIR"
            conda env create -f environment.yml 2>&1 | tail -5
        fi
    fi

    # Clone (아직 안했으면)
    if [ ! -d "$DPPD_DIR" ]; then
        git clone https://github.com/YuzheWangPKU/DiffPepBuilder.git "$DPPD_DIR"
    fi
    cd "$DPPD_DIR"

    conda activate diffpepdock 2>/dev/null || conda activate diffpepbuilder

    # 모델 가중치 다운로드
    mkdir -p experiments/checkpoints
    if [ -f "experiments/checkpoints/diffpepdock_v1.pth" ]; then
        log_ok "DiffPepDock 가중치 이미 존재"
    else
        log_info "DiffPepDock 가중치 다운로드 중..."
        wget -q --show-progress \
            "https://zenodo.org/records/15398020/files/diffpepdock_v1.pth" \
            -O experiments/checkpoints/diffpepdock_v1.pth
    fi

    # 검증
    log_info "DiffPepDock 검증 중..."
    python -c "
import torch
print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')
print('DiffPepDock setup OK')
" 2>&1

    log_ok "DiffPepDock 설치 완료"
}

# =============================================================================
# 메인
# =============================================================================
main() {
    local target="${1:-all}"

    echo "=============================================="
    echo " NIM → Local Model Setup Script"
    echo " Target: $target"
    echo " Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================="

    init_conda
    check_gpu

    case "$target" in
        all)
            setup_esmfold      # bio-tools: ESMFold + ProteinMPNN
            setup_rfdiffusion  # rfdiffusion env
            setup_diffpepdock  # diffpepdock env
            ;;
        esmfold)
            setup_esmfold
            ;;
        proteinmpnn)
            setup_proteinmpnn
            ;;
        rfdiffusion)
            setup_rfdiffusion
            ;;
        diffpepdock)
            setup_diffpepdock
            ;;
        *)
            log_err "알 수 없는 대상: $target"
            echo "사용법: $0 [all|esmfold|proteinmpnn|rfdiffusion|diffpepdock]"
            exit 1
            ;;
    esac

    echo ""
    echo "=============================================="
    log_ok "설치 완료! 환경 요약:"
    echo "  bio-tools    : ESMFold + ProteinMPNN (conda activate bio-tools)"
    echo "  rfdiffusion  : RFdiffusion            (conda activate rfdiffusion)"
    echo "  diffpepdock  : DiffPepDock             (conda activate diffpepdock)"
    echo "=============================================="
}

main "$@"
