#!/usr/bin/env bash
# =============================================================================
# auto_dispatch.sh
# harness Stage 8c — Codex/Cursor 자동 라우팅·호출·결과 보존
#
# CLAUDE.md 자동 트리거 키워드 표 기반으로 외부 CLI를 자동 dispatch.
# 결과는 _workspace/{NN}_{cli}_{topic-slug}.md로 자동 저장 (Stage 1 컨벤션).
#
# 사용법:
#   ./scripts/auto_dispatch.sh "이 backend/foo.py 코드 리뷰해줘"
#   ./scripts/auto_dispatch.sh "오늘 EOD 보고서 작성해줘"
#   ./scripts/auto_dispatch.sh --dry-run "분석해 pipeline_local/"
#   ./scripts/auto_dispatch.sh --topic offtarget-dock "선택성 점수 함수 분석"
#
# 라우팅 규칙 (CLAUDE.md §자동 트리거 키워드 표 기반):
#   - "리뷰해" (코드)           → codex review
#   - "구현해", "수정해", "테스트 생성" → codex exec
#   - "EOD", "일정", "보고"       → cursor-agent
#   - "분석해", "조사해"          → cursor-agent
#   - Claude Code 내부 에이전트(researcher, reviewer-*, engineer-*) → 본 스크립트 미지원, 안내
#
# 한계 (정직한 명시):
#   - 본 스크립트는 *외부 CLI* (codex/cursor-agent) 자동 호출만 다룬다.
#   - Claude Code 내부 서브에이전트(researcher, reviewer-*)는 본 Claude Code 세션에서 호출.
#   - 키워드 매칭은 단순 substring 기반 — 모호 입력은 미매칭으로 종료.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_DIR="$PROJECT_ROOT/_workspace"
WRAPPER="$SCRIPT_DIR/agent-wrapper.sh"

DRY_RUN=0
TOPIC_SLUG=""
PROMPT=""

# ---------------- argparse ----------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --topic)
            TOPIC_SLUG="$2"
            shift 2
            ;;
        --help|-h)
            sed -n '2,30p' "$0"
            exit 0
            ;;
        *)
            PROMPT="${PROMPT:+$PROMPT }$1"
            shift
            ;;
    esac
done

if [[ -z "${PROMPT// }" ]]; then
    echo "[error] empty prompt. Use --help." >&2
    exit 2
fi

# ---------------- routing ----------------
# 라우팅 우선순위 (Phase 5 A-4 수정):
#   1순위: 외부 CLI 명시 동사구 (리뷰해/구현해/수정해/EOD/분석해 등이 명시적 동사구로 등장)
#   2순위: 도메인 키워드 (약리학/합성/구조 등 — 동사구 없이 도메인 단어만 있을 때)
#
# 권고 휴리스틱: 외부 CLI 키워드(리뷰해/구현해/EOD/분석해)가 "명시적 동사구"로 등장하면
# 외부 CLI 우선. 단순 substring 포함만으로는 외부 CLI 안 함.
# 예: "약리학 코드 리뷰해줘" → codex:review (외부 CLI 동사구가 명시적)
#     "약리학 Boman Index 확인" → internal:reviewer-pharma (동사구 없음)
detect_route() {
    local p="$1"

    # 1) 외부 CLI 동사구 우선 매칭 (A-4: 내부 도메인 키워드보다 먼저 검사)
    #    "리뷰해" / "review" 가 명시적 동사구로 포함되어 있으면 codex:review
    if echo "$p" | grep -qE "리뷰해|review the code|code review|코드 리뷰"; then
        echo "codex:review"; return
    fi
    #    "구현해" / "수정해" / "코드 작성" / implement / fix 가 명시적 동사구
    if echo "$p" | grep -qE "구현해|수정해|코드 작성|implement|fix"; then
        echo "codex:exec"; return
    fi
    #    "테스트 생성" / write test
    if echo "$p" | grep -qE "테스트 생성|write test|add test"; then
        echo "codex:exec"; return
    fi
    #    EOD / 일정 / 상태 보고 는 cursor-agent 명시적 동사구
    if echo "$p" | grep -qE "EOD|일정|상태 보고|진행 보고"; then
        echo "cursor:prompt"; return
    fi
    #    "분석해" / "조사해" 는 cursor-agent 명시적 동사구
    if echo "$p" | grep -qE "분석해|조사해|코드 구조|analyze"; then
        echo "cursor:prompt"; return
    fi

    # 2) 도메인 키워드 내부 에이전트 매칭 (동사구 없을 때 fallback)
    if echo "$p" | grep -qE "리서치|선행 연구|문헌 비교|논문 조사|literature review"; then
        echo "internal:researcher"; return
    fi
    if echo "$p" | grep -qE "약리학|ADMET|반감기|Boman|GRAVY|Instability"; then
        echo "internal:reviewer-pharma"; return
    fi
    if echo "$p" | grep -qE "구조|SS bond|이황화결합|GPCR|수용체|binding pocket|생물활성"; then
        echo "internal:reviewer-biology"; return
    fi
    if echo "$p" | grep -qE "합성|modification|D-amino|PEG화|아실화|킬레이션|DOTA|라벨링"; then
        echo "internal:reviewer-chemistry"; return
    fi
    if echo "$p" | grep -qE "NSGA|베이지안|Bayesian|GP|Gaussian Process|최적화 알고리즘|p-value|수렴|convergence"; then
        echo "internal:reviewer-math"; return
    fi
    if echo "$p" | grep -qE "UI|UX|접근성|레이아웃|color contrast|반응형"; then
        echo "internal:reviewer-uiux"; return
    fi
    if echo "$p" | grep -qE "conda|GPU|CI|배포|환경 변경|환경 설치"; then
        echo "internal:engineer-infra"; return
    fi
    if echo "$p" | grep -qE "팀|토론|검토회의|/team"; then
        echo "internal:tmux-team"; return
    fi

    # 3) 매칭 실패
    echo "unmatched"
}

ROUTE=$(detect_route "$PROMPT")

# ---------------- topic slug 자동 생성 ----------------
if [[ -z "$TOPIC_SLUG" ]]; then
    # 첫 80자 → lowercase → 비-ASCII/특수문자 → '-' → 24자 제한
    # (한글은 의도적으로 제거 — slug는 ASCII만)
    TOPIC_SLUG=$(echo "$PROMPT" | head -c 80 \
        | LC_ALL=C tr '[:upper:]' '[:lower:]' \
        | LC_ALL=C tr -c 'a-z0-9' '-' \
        | LC_ALL=C sed -E 's/-+/-/g; s/^-+|-+$//g' \
        | head -c 24)
    [[ -z "$TOPIC_SLUG" ]] && TOPIC_SLUG="dispatched"
fi

# ---------------- 다음 NN 번호 계산 ----------------
mkdir -p "$WORKSPACE_DIR"
LAST_NN=$(ls -1 "$WORKSPACE_DIR" 2>/dev/null \
    | grep -E '^[0-9]{2}_' \
    | head -1 \
    | sed -E 's/^([0-9]{2})_.*/\1/' || echo "00")
LAST_NN=${LAST_NN:-00}
NEXT_NN=$(printf "%02d" $((10#$LAST_NN + 1)))

# ---------------- dispatch ----------------
echo ""
echo "═══════════════════════════════════════════"
echo "  auto_dispatch.sh"
echo "  prompt: ${PROMPT:0:120}"
echo "  route:  $ROUTE"
echo "  topic:  $TOPIC_SLUG"
echo "  next:   ${NEXT_NN}_<cli>_${TOPIC_SLUG}.md"
echo "═══════════════════════════════════════════"
echo ""

if [[ "$ROUTE" == internal:* ]]; then
    INTERNAL_AGENT="${ROUTE#internal:}"
    cat <<EOF
[routing] 본 입력은 **Claude Code 내부 서브에이전트** ($INTERNAL_AGENT)로 처리해야 합니다.
본 스크립트는 외부 CLI 자동 호출 전용입니다.

현재 Claude Code 세션에서 다음을 수행하세요:
  - Agent({ subagent_type: "$INTERNAL_AGENT", ... })
  - 또는 사용자에게 안내: "/team" / 적절한 트리거 키워드

산출물은 본 세션 또는 _workspace/${NEXT_NN}_${INTERNAL_AGENT}_${TOPIC_SLUG}.md 로 보존하세요.
EOF
    exit 0
fi

if [[ "$ROUTE" == "unmatched" ]]; then
    cat <<EOF
[routing] 입력 키워드가 명시적 라우팅 규칙에 매칭되지 않습니다.

다음 옵션 중 하나를 선택하세요:
  1. 명시적 prefix 추가 (예: "리뷰해 ", "구현해 ", "분석해 ")
  2. --topic 으로 명시적 topic slug 지정 후 적절한 CLI 직접 호출
  3. Claude Code 세션에서 orchestrator에 위임

unmatched_prompt: ${PROMPT}
EOF
    exit 3
fi

# 외부 CLI 호출
CLI="${ROUTE%%:*}"
SUBCMD="${ROUTE##*:}"

case "$CLI" in
    codex)
        TARGET_FILE="$WORKSPACE_DIR/${NEXT_NN}_codex_${TOPIC_SLUG}.md"
        if [[ "$DRY_RUN" -eq 1 ]]; then
            echo "[dry-run] $WRAPPER codex $SUBCMD \"$PROMPT\""
            echo "[dry-run] would write to: $TARGET_FILE"
            exit 0
        fi
        echo "# Codex dispatch output" > "$TARGET_FILE"
        echo "" >> "$TARGET_FILE"
        echo "- prompt: ${PROMPT}" >> "$TARGET_FILE"
        echo "- subcmd: $SUBCMD" >> "$TARGET_FILE"
        echo "- timestamp: $(date -Iseconds)" >> "$TARGET_FILE"
        echo "" >> "$TARGET_FILE"
        echo "## Output" >> "$TARGET_FILE"
        echo "" >> "$TARGET_FILE"
        echo '```' >> "$TARGET_FILE"
        "$WRAPPER" codex "$SUBCMD" "$PROMPT" 2>&1 | tee -a "$TARGET_FILE"
        echo '```' >> "$TARGET_FILE"
        ;;
    cursor)
        TARGET_FILE="$WORKSPACE_DIR/${NEXT_NN}_cursor-agent_${TOPIC_SLUG}.md"
        if [[ "$DRY_RUN" -eq 1 ]]; then
            echo "[dry-run] $WRAPPER cursor-agent -p \"$PROMPT\""
            echo "[dry-run] would write to: $TARGET_FILE"
            exit 0
        fi
        echo "# Cursor Agent dispatch output" > "$TARGET_FILE"
        echo "" >> "$TARGET_FILE"
        echo "- prompt: ${PROMPT}" >> "$TARGET_FILE"
        echo "- timestamp: $(date -Iseconds)" >> "$TARGET_FILE"
        echo "" >> "$TARGET_FILE"
        echo "## Output" >> "$TARGET_FILE"
        echo "" >> "$TARGET_FILE"
        echo '```' >> "$TARGET_FILE"
        "$WRAPPER" cursor-agent -p "$PROMPT" 2>&1 | tee -a "$TARGET_FILE"
        echo '```' >> "$TARGET_FILE"
        ;;
    *)
        echo "[error] unknown CLI: $CLI" >&2
        exit 4
        ;;
esac

echo ""
echo "═══════════════════════════════════════════"
echo "  결과 보존: $TARGET_FILE"
echo "═══════════════════════════════════════════"
