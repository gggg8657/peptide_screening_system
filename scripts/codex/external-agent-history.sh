#!/usr/bin/env bash
# =============================================================================
# external-agent-history.sh
# agent-wrapper 기록(history.jsonl)을 사람이 읽기 쉽게 출력합니다.
# (Codex 터미널에서 최근 codex/cursor-agent 호출 맥락 확인용)
#
# 사용법:
#   ./scripts/codex/external-agent-history.sh          # 마지막 20건
#   ./scripts/codex/external-agent-history.sh 50       # 마지막 N건
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/logs/external_agents"
N="${1:-20}"

if [[ ! -f "$LOG_DIR/history.jsonl" ]]; then
    echo "[info] 아직 기록 없음: $LOG_DIR/history.jsonl"
    echo "       먼저 ./scripts/agent-wrapper.sh … 를 실행하세요."
    exit 0
fi

python3 -c "
import json
from collections import deque
n = int('$N')
path = '$LOG_DIR/history.jsonl'
lines = deque(maxlen=n)
with open(path) as f:
    for line in f:
        line = line.strip()
        if line:
            lines.append(line)
for raw in list(lines):
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        print(raw[:200])
        continue
    st = 'OK' if d.get('exit_code') == 0 else 'FAIL'
    print(f\"{st} | {d.get('agent','?')} | {d.get('duration_s',0)}s | {d.get('timestamp','')}\")
    print(f\"     {d.get('args','')[:120]}\")
    print(f\"     session: {d.get('session_id','')}\")
"
