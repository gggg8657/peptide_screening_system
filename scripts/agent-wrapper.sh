#!/usr/bin/env bash
# =============================================================================
# agent-wrapper.sh
# codex / cursor-agent 호출을 로깅하는 래퍼 (jq 미사용)
#
# 사용법:
#   ./scripts/agent-wrapper.sh codex exec "뭐뭐해"
#   ./scripts/agent-wrapper.sh codex review
#   ./scripts/agent-wrapper.sh cursor-agent -p "뭐뭐해"
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs/external_agents"
mkdir -p "$LOG_DIR"

AGENT="$1"
shift
ARGS=("$@")
ARGS_TEXT="$*"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SESSION_ID="${AGENT}_${TIMESTAMP}_$$"
LOG_FILE="$LOG_DIR/${SESSION_ID}.jsonl"
START_EPOCH=$(date +%s)

# 시작 로그 (python3 사용, jq 불필요)
python3 -c "
import json, sys
print(json.dumps({
    'type': 'start',
    'agent': sys.argv[1],
    'args': sys.argv[2],
    'timestamp': sys.argv[3],
    'session_id': sys.argv[4]
}))
" "$AGENT" "$ARGS_TEXT" "$(date -Iseconds)" "$SESSION_ID" >> "$LOG_FILE"

echo ""
echo "═══════════════════════════════════════════"
echo "  [${AGENT}] 작업 할당"
echo "  내용: ${ARGS_TEXT:0:120}"
echo "  로그: $LOG_FILE"
echo "═══════════════════════════════════════════"
echo ""

# 실행 + 출력 캡처
TEMP_OUT=$(mktemp)
set +e
if [ "$AGENT" = "codex" ]; then
    # codex exec은 프롬프트를 단일 인자로 전달해야 함
    SUBCMD="${ARGS[0]:-exec}"
    if [ "$SUBCMD" = "review" ]; then
        codex review "${ARGS[@]:1}" </dev/null 2>&1 | tee "$TEMP_OUT"
    elif [ "$SUBCMD" = "exec" ]; then
        codex exec --dangerously-bypass-approvals-and-sandbox "${ARGS[@]:1}" </dev/null 2>&1 | tee "$TEMP_OUT"
    else
        # exec 생략 시 전체를 프롬프트로
        codex exec --dangerously-bypass-approvals-and-sandbox "$ARGS_TEXT" </dev/null 2>&1 | tee "$TEMP_OUT"
    fi
elif [ "$AGENT" = "cursor-agent" ]; then
    cursor-agent "${ARGS[@]}" </dev/null 2>&1 | tee "$TEMP_OUT"
else
    "$AGENT" "${ARGS[@]}" </dev/null 2>&1 | tee "$TEMP_OUT"
fi
EXIT_CODE=${PIPESTATUS[0]}
set -e

# 결과 로그
OUTPUT=$(head -c 50000 "$TEMP_OUT")  # 50KB 제한
rm -f "$TEMP_OUT"

END_EPOCH=$(date +%s)
DURATION=$(( END_EPOCH - START_EPOCH ))

python3 -c "
import json, sys
print(json.dumps({
    'type': 'end',
    'agent': sys.argv[1],
    'output': sys.argv[2][:5000],
    'exit_code': int(sys.argv[3]),
    'timestamp': sys.argv[4],
    'session_id': sys.argv[5],
    'duration_s': int(sys.argv[6])
}))
" "$AGENT" "$OUTPUT" "$EXIT_CODE" "$(date -Iseconds)" "$SESSION_ID" "$DURATION" >> "$LOG_FILE"

# 히스토리 로그 (최근 목록용)
python3 -c "
import json, sys
print(json.dumps({
    'agent': sys.argv[1],
    'args': sys.argv[2][:200],
    'exit_code': int(sys.argv[3]),
    'timestamp': sys.argv[4],
    'session_id': sys.argv[5],
    'duration_s': int(sys.argv[6])
}))
" "$AGENT" "$ARGS_TEXT" "$EXIT_CODE" "$(date -Iseconds)" "$SESSION_ID" "$DURATION" >> "$LOG_DIR/history.jsonl"

echo ""
echo "═══════════════════════════════════════════"
echo "  [${AGENT}] 결과 수신"
echo "  종료코드: $EXIT_CODE"
echo "  소요시간: ${DURATION}초"
echo "═══════════════════════════════════════════"
echo ""
