#!/usr/bin/env bash
# =============================================================================
# test_auto_dispatch_routing.sh
# harness Stage 8e (VR-cycle-04 closure) — auto_dispatch.sh 라우팅 회귀 테스트
#
# CLAUDE.md 자동 트리거 키워드 표 기반의 routing 정확도를 자동 검증.
# 16개 표준 케이스(외부 동사구 / 내부 도메인 / 모호 / unmatched) × expected route
# 매트릭스로 PASS/FAIL 보고. exit code 0 = 전수 PASS, 1 = 1건 이상 FAIL.
#
# 사용법:
#   ./scripts/test_auto_dispatch_routing.sh           # 전수 테스트
#   ./scripts/test_auto_dispatch_routing.sh --quiet   # PASS는 숨김
# =============================================================================

set -uo pipefail  # 단, -e는 미설정 — 한 케이스 FAIL도 다른 케이스 계속

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISPATCH="$SCRIPT_DIR/auto_dispatch.sh"

QUIET=0
[[ "${1:-}" == "--quiet" ]] && QUIET=1

# ---------------- 표준 테스트 케이스 ----------------
# 형식: "expected_route|prompt"

CASES=(
    # === 외부 CLI 명시 동사구 (codex:review) ===
    "codex:review|backend/foo.py 코드 리뷰해줘"
    "codex:review|please review the code in scripts/bar.py"

    # === 외부 CLI 명시 동사구 (codex:exec) ===
    "codex:exec|새 함수 hello() 구현해줘"
    "codex:exec|이 버그 수정해 — None 검사 빠짐"
    "codex:exec|write test for utils.format_date"

    # === 외부 CLI 명시 동사구 (cursor:prompt) ===
    "cursor:prompt|오늘 EOD 보고서 작성"
    "cursor:prompt|pipeline_local/ 디렉토리 구조 분석해"

    # === 내부 도메인 키워드 (동사구 없음) ===
    "internal:reviewer-pharma|Boman Index 부호 확인"
    "internal:reviewer-pharma|ADMET 평가 결과 검토"
    "internal:reviewer-biology|SS bond 토폴로지 확인"
    "internal:reviewer-chemistry|PEG화 화학 충돌 가능성"
    "internal:reviewer-math|NSGA-II 수렴 진단"
    "internal:researcher|GLP-1 작용제 선행 연구 조사"

    # === 외부 동사구 + 도메인 단어 동시 (외부 우선 — VR-cycle-04 핵심) ===
    "codex:review|약리학 모듈 코드 리뷰해줘"
    "codex:exec|modification 충돌 검사 함수 수정해"

    # === unmatched (자동 추측 차단) ===
    "unmatched|오늘 날씨가 어때"
)

# ---------------- 실행 ----------------
n_pass=0
n_fail=0
failures=()

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "  auto_dispatch.sh routing 회귀 테스트 (VR-cycle-04 closure)"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

for case in "${CASES[@]}"; do
    expected="${case%%|*}"
    prompt="${case##*|}"

    # auto_dispatch --dry-run 으로 라우팅만 측정
    output=$("$DISPATCH" --dry-run "$prompt" 2>&1 || true)
    actual=$(echo "$output" | grep -oE 'route:[[:space:]]+[a-z:-]+' | head -1 | sed -E 's/route:[[:space:]]+//')

    if [[ "$actual" == "$expected" ]]; then
        n_pass=$((n_pass + 1))
        if [[ "$QUIET" -eq 0 ]]; then
            printf "  [+] %-30s | %s\n" "$expected" "${prompt:0:50}"
        fi
    else
        n_fail=$((n_fail + 1))
        printf "  [X] expected=%-22s actual=%-22s | %s\n" "$expected" "$actual" "${prompt:0:50}"
        failures+=("$prompt — expected=$expected, actual=$actual")
    fi
done

echo ""
echo "───────────────────────────────────────────────────────────────────────"
echo "  Total: $n_pass/${#CASES[@]} PASS"

if [[ "$n_fail" -gt 0 ]]; then
    echo ""
    echo "  FAILURES:"
    for f in "${failures[@]}"; do
        echo "    - $f"
    done
    echo ""
    exit 1
fi

echo ""
exit 0
