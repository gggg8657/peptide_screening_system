#!/usr/bin/env bash
# pepADMET 전 모델 재현을 위한 데이터/코드 다운로드 스크립트
# 총 예상 용량: ~4-5GB (conda env 포함)
#
# 사용법:
#   온라인:   bash scripts/download_pepadmet.sh
#   오프라인 이식: bash scripts/download_pepadmet.sh --pack
#
# 디렉토리 구조:
#   local_models/pepadmet/
#   ├── repo/                 ← GitHub clone (코드 + 독성 모델 .pth)
#   ├── data/
#   │   ├── rt_pretrain/      ← RT DB ~350K (Transfer Learning pre-train)
#   │   ├── halflife/         ← PEPlife2 + PepTherDia (fine-tune)
#   │   ├── permeability/     ← CycPeptMPDB + PAMPA
#   │   ├── bbb/              ← B3Pdb + Brainpeps
#   │   ├── toxicity/         ← DBAASP + Hemolytik (repo에 포함)
#   │   └── other/            ← LogD, F, UniProt sequences
#   └── env/                  ← conda-pack 결과 (오프라인 이식용)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PEPADMET_DIR="$PROJECT_ROOT/local_models/pepadmet"
DATA_DIR="$PEPADMET_DIR/data"
PACK_MODE=false

if [[ "${1:-}" == "--pack" ]]; then
    PACK_MODE=true
    echo "=== PACK MODE: conda env를 tar.gz로 패킹합니다 ==="
fi

echo "============================================"
echo " pepADMET 전 모델 재현 다운로드 스크립트"
echo " 예상 총 용량: ~4-5GB"
echo " 대상 디렉토리: $PEPADMET_DIR"
echo "============================================"
echo ""

# ─── 1. 디렉토리 생성 ───
mkdir -p "$DATA_DIR"/{rt_pretrain,halflife,permeability,bbb,toxicity,other}

# ─── 2. GitHub 레포 클론 ───
echo "[1/7] pepADMET GitHub 레포 클론..."
if [ -d "$PEPADMET_DIR/repo/.git" ]; then
    echo "  → 이미 클론됨. pull 실행."
    cd "$PEPADMET_DIR/repo" && git pull && cd "$PROJECT_ROOT"
else
    git clone https://github.com/ifyoungnet/pepADMET.git "$PEPADMET_DIR/repo"
fi
echo "  → 완료 (코드 + toxicity_early_stop.pth 포함)"
echo ""

# ─── 3. conda env 생성 ───
echo "[2/7] conda env 'pepadmet' 생성..."
if conda env list | grep -q "pepadmet"; then
    echo "  → 이미 존재. 스킵."
else
    conda create -n pepadmet python=3.7.16 -y
    conda run -n pepadmet pip install \
        torch==1.13.1+cu117 \
        -f https://download.pytorch.org/whl/torch_stable.html
    conda run -n pepadmet pip install \
        dgl==0.4.3 \
        scikit-learn==1.0.2 \
        numpy==1.21.5 \
        pandas==1.3.5 \
        tqdm==4.65.0 \
        rdkit-pypi==2022.9.5 \
        modlamp==4.3.0 \
        openbabel-wheel==3.1.1.1
    # PyBioMed — pip 설치 (버전 호환 문제 시 GitHub에서 직접)
    conda run -n pepadmet pip install PyBioMed || {
        echo "  → PyBioMed pip 실패, GitHub에서 직접 설치..."
        conda run -n pepadmet pip install git+https://github.com/gadsbyfly/PyBioMed.git
    }
fi
echo "  → 완료"
echo ""

# ─── 4. RT DB (Transfer Learning pre-train, ~350K) ───
echo "[3/7] RT (Retention Time) DB 다운로드 (~350K entries)..."
echo "  출처: ProteomeTools / AlphaPeptDeep 관련 공개 데이터"
RT_DIR="$DATA_DIR/rt_pretrain"

# ProteomeTools synthetic peptide RT 데이터 (PRIDE Archive)
# PXD004732: ProteomeTools Part 1 (synthetic peptides, ~350K)
if [ ! -f "$RT_DIR/proteometools_rt.csv" ]; then
    echo "  → ProteomeTools RT 데이터 다운로드..."
    echo "  주의: PRIDE Archive에서 직접 다운로드 필요 (자동화 불가할 수 있음)"
    echo "  수동 다운로드 URL: https://www.ebi.ac.uk/pride/archive/projects/PXD004732"
    echo ""
    echo "  대안: AlphaPeptDeep 사전학습 데이터 활용"
    # AlphaPeptDeep RT prediction 학습 데이터
    if command -v wget &>/dev/null; then
        wget -q --show-progress -O "$RT_DIR/alphapeptdeep_rt_train.zip" \
            "https://github.com/MannLabs/alphapeptdeep/raw/main/nbs/data/rt_train.zip" 2>/dev/null || {
            echo "  → AlphaPeptDeep RT 데이터 직접 다운로드 불가."
            echo "  → 수동 다운로드 필요: https://github.com/MannLabs/alphapeptdeep"
        }
        if [ -f "$RT_DIR/alphapeptdeep_rt_train.zip" ]; then
            unzip -q -o "$RT_DIR/alphapeptdeep_rt_train.zip" -d "$RT_DIR/" 2>/dev/null || true
        fi
    fi
    # 추가: Chronologer RT prediction 데이터 (Searle Lab)
    echo "  참고: Chronologer (https://github.com/searlelab/chronologer) 도 RT 데이터 보유"
else
    echo "  → 이미 존재. 스킵."
fi
echo ""

# ─── 5. Half-life 데이터 (fine-tune, 970개) ───
echo "[4/7] Half-life 학습 데이터 수집..."
HL_DIR="$DATA_DIR/halflife"

# PEPlife2 REST API (Raghava 그룹)
if [ ! -f "$HL_DIR/peplife2_dump.json" ]; then
    echo "  → PEPlife2 DB 조회 시도..."
    # PEPlife2 API: http://webs.iiitd.edu.in/raghava/peplife2/api.php
    curl -sS --max-time 30 \
        "http://webs.iiitd.edu.in/raghava/peplife2/api.php?dataType=all" \
        -o "$HL_DIR/peplife2_dump.json" 2>/dev/null || {
        echo "  → PEPlife2 API 접근 실패 (서버 다운 가능). 수동 수집 필요."
        echo "  → URL: http://webs.iiitd.edu.in/raghava/peplife2/"
    }
fi

# PepTherDia (D'Aloisio 2021)
if [ ! -f "$HL_DIR/peptherdia_note.txt" ]; then
    echo "  → PepTherDia: 수동 다운로드 필요"
    cat > "$HL_DIR/peptherdia_note.txt" << 'HEREDOC'
PepTherDia 데이터 수집 안내
===========================
URL: https://peptherdia.herokuapp.com/ (또는 후속 URL)
논문: D'Aloisio et al., Drug Discovery Today, 2021, 26, 1409-1419
필요 데이터: 치료 펩타이드 PK 파라미터 (T_1/2, clearance 등)
수집 방법: 웹 인터페이스에서 CSV 다운로드 또는 논문 supplementary
HEREDOC
fi

# THPdb (Usmani 2017)
if [ ! -f "$HL_DIR/thpdb_note.txt" ]; then
    echo "  → THPdb: 수동 다운로드 필요"
    cat > "$HL_DIR/thpdb_note.txt" << 'HEREDOC'
THPdb 데이터 수집 안내
======================
URL: https://webs.iiitd.edu.in/raghava/thpdb/
논문: Usmani et al., PLoS One, 2017, 12, e0181748
필요 데이터: FDA-approved therapeutic peptide 데이터 (반감기 포함)
수집 방법: Browse → Download 또는 API
HEREDOC
fi
echo "  → Half-life 데이터 디렉토리 준비 완료"
echo ""

# ─── 6. Permeability 데이터 ───
echo "[5/7] Permeability 학습 데이터..."
PERM_DIR="$DATA_DIR/permeability"

# CycPeptMPDB (Li 2023) — cyclic peptide membrane permeability
if [ ! -f "$PERM_DIR/cycpeptmpdb_note.txt" ]; then
    cat > "$PERM_DIR/cycpeptmpdb_note.txt" << 'HEREDOC'
CycPeptMPDB 데이터 수집 안내
============================
URL: http://cycpeptmpdb.com/
논문: Li et al., J. Chem. Inf. Model. 2023, 63, 2240-2250
데이터: PAMPA (6,698), RRCK (181), Caco-2 (886+645+241)
수집: Download 페이지 또는 논문 supplementary
HEREDOC
fi
echo "  → Permeability 데이터 안내 파일 생성"
echo ""

# ─── 7. BBB / LogD / F 데이터 ───
echo "[6/7] BBB / LogD / Bioavailability 데이터..."
BBB_DIR="$DATA_DIR/bbb"

# B3Pdb (Van Dorpe 2012)
if [ ! -f "$BBB_DIR/bbb_data_note.txt" ]; then
    cat > "$BBB_DIR/bbb_data_note.txt" << 'HEREDOC'
BBB Penetration 데이터 수집 안내
================================
B3Pdb: https://webs.iiitd.edu.in/raghava/b3pdb/ (Kumar 2021)
  - 850 BBB peptides (425 positive / 425 negative)
Brainpeps: 논문에서 참조 (Van Dorpe 2012)
  - Brain Struct. Funct. 2012, 217, 687-718
수집: 웹 다운로드 또는 논문 supplementary
HEREDOC
fi

# LogD / F 데이터
if [ ! -f "$DATA_DIR/other/logd_f_note.txt" ]; then
    cat > "$DATA_DIR/other/logd_f_note.txt" << 'HEREDOC'
LogD_7.4 / Bioavailability(F) 데이터 수집 안내
===============================================
LogD_7.4: 257 entries — 논문 supplementary 또는 pepADMET documentation
F (경구 생체이용률): 305 entries (117 positive / 188 negative)
출처: pepADMET 논문 Methods 섹션 참조
HEREDOC
fi
echo "  → BBB/LogD/F 데이터 안내 파일 생성"
echo ""

# ─── 요약 ───
echo "[7/7] 다운로드 현황 요약..."
echo ""
echo "=== pepADMET 재현 데이터 현황 ==="
echo ""
echo "자동 다운로드 완료:"
echo "  ✅ GitHub repo (코드 + 독성 모델 .pth)"
echo "  ✅ conda env 'pepadmet' (Python 3.7 + PyTorch + DGL)"
echo ""
echo "수동 수집 필요:"
echo "  📋 RT DB ~350K    → ProteomeTools PXD004732 또는 AlphaPeptDeep"
echo "  📋 PEPlife2       → API 또는 웹 ($HL_DIR/)"
echo "  📋 CycPeptMPDB    → http://cycpeptmpdb.com/"
echo "  📋 B3Pdb          → https://webs.iiitd.edu.in/raghava/b3pdb/"
echo "  📋 PepTherDia     → 논문 supplementary"
echo "  📋 THPdb          → https://webs.iiitd.edu.in/raghava/thpdb/"
echo ""

# ─── conda pack (오프라인 이식) ───
if $PACK_MODE; then
    echo "=== conda-pack 실행 ==="
    conda run -n pepadmet pip install conda-pack 2>/dev/null || conda install -n base conda-pack -y
    mkdir -p "$PEPADMET_DIR/env"
    conda pack -n pepadmet -o "$PEPADMET_DIR/env/pepadmet_env.tar.gz" --force
    echo "  → $PEPADMET_DIR/env/pepadmet_env.tar.gz 생성 완료"
    ls -lh "$PEPADMET_DIR/env/pepadmet_env.tar.gz"
fi

echo ""
echo "=== 완료 ==="
echo "다음 단계:"
echo "  1. 수동 수집 데이터를 $DATA_DIR/ 하위에 배치"
echo "  2. conda activate pepadmet"
echo "  3. cd $PEPADMET_DIR/repo && python calculate_descriptors.py"
echo "  4. 각 모델별 학습 스크립트 실행 (Train.ipynb 참조)"
