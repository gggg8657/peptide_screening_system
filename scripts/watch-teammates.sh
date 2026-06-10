#!/usr/bin/env bash
# =============================================================================
# watch-teammates.sh — teammate 활동 실시간 모니터링
#
# 사용법:
#   ./scripts/watch-teammates.sh          # 실시간 감시
#   ./scripts/watch-teammates.sh history   # 최근 이력 조회
# =============================================================================

LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../logs/external_agents"
mkdir -p "$LOG_DIR"

if [ "${1:-}" = "history" ]; then
    echo "═══ Teammate 실행 이력 ═══"
    if [ -f "$LOG_DIR/history.jsonl" ]; then
        python3 -c "
import json, sys
for line in open('$LOG_DIR/history.jsonl'):
    try:
        d = json.loads(line.strip())
        status = '✅' if d.get('exit_code', 1) == 0 else '❌'
        print(f\"{status} [{d['agent']}] {d.get('duration_s',0)}s | {d['args'][:80]} | {d['timestamp']}\")
    except: pass
"
    else
        echo "(이력 없음)"
    fi
    exit 0
fi

echo "═══ Teammate 활동 실시간 감시 (Ctrl+C로 종료) ═══"
echo "로그 디렉토리: $LOG_DIR"
echo ""

# 새 파일이 생기면 자동 감지
if command -v inotifywait &>/dev/null; then
    tail -f "$LOG_DIR"/*.jsonl 2>/dev/null | python3 -c "
import json, sys
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        t = d.get('type', '?')
        agent = d.get('agent', '?')
        if t == 'start':
            print(f'🚀 [{agent}] 시작: {d.get(\"args\",\"\")[:100]}')
        elif t == 'end':
            code = d.get('exit_code', -1)
            dur = d.get('duration_s', 0)
            icon = '✅' if code == 0 else '❌'
            print(f'{icon} [{agent}] 완료 ({dur}s, exit={code})')
            out = d.get('output', '')[:200]
            if out:
                print(f'   └─ {out[:150]}')
    except: pass
    sys.stdout.flush()
"
else
    # inotifywait 없으면 polling
    tail -f "$LOG_DIR"/*.jsonl 2>/dev/null | while read line; do
        echo "$line" | python3 -c "
import json, sys
line = sys.stdin.read().strip()
try:
    d = json.loads(line)
    t = d.get('type', '?')
    agent = d.get('agent', '?')
    if t == 'start':
        print(f'🚀 [{agent}] 시작: {d.get(\"args\",\"\")[:100]}')
    elif t == 'end':
        code = d.get('exit_code', -1)
        dur = d.get('duration_s', 0)
        icon = '✅' if code == 0 else '❌'
        print(f'{icon} [{agent}] 완료 ({dur}s, exit={code})')
except: pass
" 2>/dev/null
    done
fi
