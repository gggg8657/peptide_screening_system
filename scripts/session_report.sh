#!/usr/bin/env bash
# =============================================================================
# session_report.sh — 다른 세션·worktree 진행상황 + 보고자료 통합 집계
# =============================================================================
#
# Usage:
#   bash scripts/session_report.sh                  # 화면 출력
#   bash scripts/session_report.sh --save           # _workspace/release/ 저장
#   bash scripts/session_report.sh --save <path>    # 지정 경로 저장
#   bash scripts/session_report.sh --section pr     # 특정 섹션만
#
# Sections: worktree | dirty | pr | eod | pptx | all (기본)
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SAVE=0
SAVE_PATH=""
SECTION="all"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --save)
            SAVE=1
            shift
            if [[ $# -gt 0 && "$1" != --* ]]; then
                SAVE_PATH="$1"
                shift
            fi
            ;;
        --section)
            SECTION="$2"
            shift 2
            ;;
        -h|--help)
            sed -n '3,16p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown arg: $1" >&2
            exit 1
            ;;
    esac
done

TODAY="$(date +%Y-%m-%d)"
NOW="$(date '+%Y-%m-%d %H:%M:%S')"

if [[ $SAVE -eq 1 && -z "$SAVE_PATH" ]]; then
    SAVE_PATH="_workspace/release/session-overview-${TODAY}.md"
fi

OUT=""
emit() { OUT+="$1"$'\n'; }

emit "# 세션 통합 보고 — ${NOW}"
emit ""
emit "_생성: \`scripts/session_report.sh\` · 호스트: $(hostname) · 브랜치: $(git branch --show-current)_"
emit ""

# -----------------------------------------------------------------------------
# 1. Worktree 현황
# -----------------------------------------------------------------------------
if [[ "$SECTION" == "all" || "$SECTION" == "worktree" || "$SECTION" == "dirty" ]]; then
    emit "## 1. Worktree 현황"
    emit ""
    emit "| Worktree | 브랜치 | Dirty | 최근 활동 | 최신 커밋 |"
    emit "|---|---|---|---|---|"

    while IFS= read -r wt; do
        [[ -z "$wt" || ! -d "$wt" ]] && continue
        [[ "$wt" == "$REPO_ROOT" ]] && continue
        branch=$(git -C "$wt" branch --show-current 2>/dev/null || echo "?")
        dirty=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        last_rel=$(git -C "$wt" log -1 --format="%cr" 2>/dev/null || echo "?")
        last_msg=$(git -C "$wt" log -1 --format="%s" 2>/dev/null | head -c 60)
        short=$(basename "$wt")
        flag=""
        [[ "$dirty" != "0" ]] && flag=" ⚠️"
        emit "| ${short} | ${branch} | ${dirty}${flag} | ${last_rel} | ${last_msg} |"
    done < <(git worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2}')
    emit ""
fi

# -----------------------------------------------------------------------------
# 2. Dirty worktree 상세 (잃을 수 있는 변경)
# -----------------------------------------------------------------------------
if [[ "$SECTION" == "all" || "$SECTION" == "dirty" ]]; then
    emit "## 2. 미커밋 변경 (점검 필요)"
    emit ""
    HAS_DIRTY=0
    while IFS= read -r wt; do
        [[ -z "$wt" || ! -d "$wt" ]] && continue
        dirty=$(git -C "$wt" status --porcelain 2>/dev/null)
        [[ -z "$dirty" ]] && continue
        HAS_DIRTY=1
        short=$(basename "$wt")
        branch=$(git -C "$wt" branch --show-current 2>/dev/null)
        emit "### ${short} (\`${branch}\`)"
        emit ""
        emit '```'
        emit "$dirty"
        emit '```'
        emit ""
    done < <(git worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2}')
    [[ $HAS_DIRTY -eq 0 ]] && { emit "_모든 worktree clean._"; emit ""; }
fi

# -----------------------------------------------------------------------------
# 3. OPEN PR
# -----------------------------------------------------------------------------
if [[ "$SECTION" == "all" || "$SECTION" == "pr" ]]; then
    emit "## 3. OPEN PR"
    emit ""
    if command -v gh >/dev/null 2>&1; then
        prs=$(gh pr list --state open --limit 50 \
            --json number,title,headRefName,isDraft,updatedAt,author \
            2>/dev/null || echo "[]")
        if [[ "$prs" != "[]" && -n "$prs" ]]; then
            emit "| # | 상태 | 업데이트 | 브랜치 | 제목 |"
            emit "|---|---|---|---|---|"
            echo "$prs" | python3 -c "
import json, sys, datetime
data = json.load(sys.stdin)
now = datetime.datetime.now(datetime.timezone.utc)
for p in sorted(data, key=lambda x: x['updatedAt'], reverse=True):
    state = 'DRAFT' if p['isDraft'] else 'OPEN'
    upd = p['updatedAt'][:10]
    upd_dt = datetime.datetime.fromisoformat(p['updatedAt'].replace('Z', '+00:00'))
    days = (now - upd_dt).days
    flag = ' ⚠️' if days > 5 else ''
    print(f\"| #{p['number']} | {state}{flag} | {upd} ({days}d) | {p['headRefName'][:45]} | {p['title'][:55]} |\")
" >> /tmp/_report_pr.$$
            while IFS= read -r line; do emit "$line"; done < /tmp/_report_pr.$$
            rm -f /tmp/_report_pr.$$
        else
            emit "_OPEN PR 없음._"
        fi
    else
        emit "_gh CLI 없음 — PR 섹션 스킵._"
    fi
    emit ""
fi

# -----------------------------------------------------------------------------
# 4. 최근 EOD/SOD (_workspace/release/)
# -----------------------------------------------------------------------------
if [[ "$SECTION" == "all" || "$SECTION" == "eod" ]]; then
    emit "## 4. 최근 EOD/SOD (최근 10개)"
    emit ""
    emit "| 종류 | 날짜 | 파일 | 크기 |"
    emit "|---|---|---|---|"
    while read -r ts path; do
        [[ -z "$path" ]] && continue
        fname=$(basename "$path")
        size=$(stat -c%s "$path" 2>/dev/null || echo "?")
        kind=$(echo "$fname" | grep -oE '^(eod|sod)' | tr '[:lower:]' '[:upper:]')
        date_part=$(echo "$fname" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
        emit "| ${kind} | ${date_part} | [\`${fname}\`](_workspace/release/${fname}) | $((size / 1024))KB |"
    done < <(find _workspace/release -maxdepth 1 -type f \
        \( -name "eod-*.md" -o -name "sod-*.md" \) -printf "%T@ %p\n" 2>/dev/null \
        | sort -rn | head -10)
    emit ""
fi

# -----------------------------------------------------------------------------
# 5. 보고자료 (PPTX)
# -----------------------------------------------------------------------------
if [[ "$SECTION" == "all" || "$SECTION" == "pptx" ]]; then
    emit "## 5. 보고자료 (PPTX)"
    emit ""
    emit "| 파일 | 크기 | 수정일 |"
    emit "|---|---|---|"
    while read -r ts size path; do
        [[ -z "$path" ]] && continue
        fname=$(basename "$path")
        rel="${path#./}"
        mtime=$(stat -c%y "$path" 2>/dev/null | cut -d' ' -f1)
        emit "| [\`${fname}\`](${rel}) | $((size / 1024))KB | ${mtime} |"
    done < <(find _workspace -type f -name "*.pptx" -not -path "*/node_modules/*" \
        -printf "%T@ %s %p\n" 2>/dev/null | sort -rn)
    emit ""
fi

# -----------------------------------------------------------------------------
# 6. 요약
# -----------------------------------------------------------------------------
if [[ "$SECTION" == "all" ]]; then
    emit "## 6. 요약"
    emit ""
    wt_count=$(git worktree list 2>/dev/null | wc -l | tr -d ' ')
    dirty_count=0
    while IFS= read -r wt; do
        [[ -z "$wt" || ! -d "$wt" ]] && continue
        cnt=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        [[ "$cnt" != "0" ]] && dirty_count=$((dirty_count + 1))
    done < <(git worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2}')

    pr_count=0
    if command -v gh >/dev/null 2>&1; then
        pr_count=$(gh pr list --state open --limit 50 --json number 2>/dev/null \
            | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo 0)
    fi
    pptx_count=$(find _workspace -type f -name "*.pptx" -not -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')

    emit "- Worktree: **${wt_count}개** (dirty **${dirty_count}개**)"
    emit "- OPEN PR: **${pr_count}개**"
    emit "- PPTX 보고자료: **${pptx_count}개**"
    emit ""
fi

# -----------------------------------------------------------------------------
# 출력
# -----------------------------------------------------------------------------
if [[ $SAVE -eq 1 ]]; then
    mkdir -p "$(dirname "$SAVE_PATH")"
    printf "%s" "$OUT" > "$SAVE_PATH"
    echo "✅ 저장: $SAVE_PATH" >&2
    echo "$SAVE_PATH"
else
    printf "%s" "$OUT"
fi
