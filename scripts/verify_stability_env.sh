#!/usr/bin/env bash
# scripts/verify_stability_env.sh
#
# bio-tools 환경의 stability predictor 의존성 검증
# 대상: peptides.py 0.5.0 + Biopython ProteinAnalysis
#
# 사용법:
#   bash scripts/verify_stability_env.sh
#   bash scripts/verify_stability_env.sh --verbose

set -euo pipefail

VERBOSE=false
if [[ "${1:-}" == "--verbose" ]]; then
    VERBOSE=true
fi

PASS=0
FAIL=0

check() {
    local label="$1"
    local result="$2"
    local expected="$3"  # 옵션 — 결과 출력용
    echo "  [$label] $result"
    PASS=$((PASS + 1))
}

fail() {
    local label="$1"
    local msg="$2"
    echo "  ❌ [$label] FAIL: $msg" >&2
    FAIL=$((FAIL + 1))
}

echo "======================================================"
echo " bio-tools 환경 stability 의존성 검증"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"
echo ""

# ─── 1. conda env 존재 확인 ───
echo "[1/4] conda env 확인..."
if conda env list | grep -q "^bio-tools"; then
    echo "  ✅ bio-tools env 존재"
    PASS=$((PASS + 1))
else
    fail "bio-tools env" "conda env 'bio-tools' 없음"
fi
echo ""

# ─── 2. Biopython 검증 ───
echo "[2/4] Biopython ProteinAnalysis..."
BIOPYTHON_RESULT=$(conda run -n bio-tools python -c "
from Bio.SeqUtils.ProtParam import ProteinAnalysis
seq = 'AICKNFFWKTFTSC'
pa = ProteinAnalysis(seq)
gravy = round(pa.gravy(), 4)
mw = round(pa.molecular_weight(), 2)
ii = round(pa.instability_index(), 2)
print(f'GRAVY={gravy}  MW={mw}  InstabilityIndex={ii}')
" 2>&1)

if echo "$BIOPYTHON_RESULT" | grep -q "GRAVY="; then
    echo "  ✅ Biopython ProteinAnalysis: $BIOPYTHON_RESULT"
    PASS=$((PASS + 1))
else
    fail "Biopython" "$BIOPYTHON_RESULT"
fi
echo ""

# ─── 3. peptides.py 검증 ───
echo "[3/4] peptides.py (v0.5.0) 검증..."
PEPTIDES_RESULT=$(conda run -n bio-tools python -c "
import peptides
from peptides import Peptide
seq = 'AICKNFFWKTFTSC'
pep = Peptide(seq)
boman     = round(pep.boman(), 4)
aliphatic = round(pep.aliphatic_index(), 4)
charge    = round(pep.charge(pH=7.4), 4)
hydro     = round(pep.hydrophobicity(), 4)
instab    = round(pep.instability_index(), 4)
version   = peptides.__version__
print(f'version={version}  Boman={boman}  Aliphatic={aliphatic}  Charge={charge}  Hydro={hydro}  Instab={instab}')
" 2>&1)

if echo "$PEPTIDES_RESULT" | grep -q "version="; then
    echo "  ✅ peptides.py: $PEPTIDES_RESULT"
    PASS=$((PASS + 1))
else
    fail "peptides.py" "$PEPTIDES_RESULT"
fi
echo ""

# ─── 4. 통합 검증 (stability_predictor 예상 사용 패턴) ───
echo "[4/4] 통합 검증 (stability_predictor.py 예상 패턴)..."
INTEGRATION_RESULT=$(conda run -n bio-tools python -c "
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from peptides import Peptide

def compute_stability(seq: str) -> dict:
    pa = ProteinAnalysis(seq)
    pep = Peptide(seq)
    return {
        'gravy':              round(pa.gravy(), 4),
        'instability_index':  round(pa.instability_index(), 4),
        'boman_index':        round(pep.boman(), 4),
        'aliphatic_index':    round(pep.aliphatic_index(), 4),
        'charge_ph74':        round(pep.charge(pH=7.4), 4),
        'hydrophobicity':     round(pep.hydrophobicity(), 4),
        'molecular_weight':   round(pa.molecular_weight(), 2),
    }

result = compute_stability('AICKNFFWKTFTSC')
for k, v in result.items():
    print(f'  {k}: {v}')
print('✅ 통합 검증 완료')
" 2>&1)

if echo "$INTEGRATION_RESULT" | grep -q "통합 검증 완료"; then
    if $VERBOSE; then
        echo "$INTEGRATION_RESULT"
    else
        echo "  ✅ stability_predictor 패턴 정상 작동"
    fi
    PASS=$((PASS + 1))
else
    fail "통합 검증" "$INTEGRATION_RESULT"
fi
echo ""

# ─── 결과 요약 ───
echo "======================================================"
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    echo " ✅ 전체 통과: $PASS/$TOTAL"
    echo " bio-tools env stability 의존성 준비 완료"
else
    echo " ❌ 실패: $FAIL/$TOTAL"
    echo " 위 오류를 확인하고 패키지 재설치 필요:"
    echo "   conda run -n bio-tools pip install peptides==0.5.0"
fi
echo "======================================================"
echo ""
echo "참고:"
echo "  - peptides.py 0.5.0: gravy() 메서드 없음 → Biopython ProteinAnalysis.gravy() 사용"
echo "  - pepADMET: PyPI 미배포, 별도 conda env 'pepadmet' 권장 (scripts/download_pepadmet.sh)"
