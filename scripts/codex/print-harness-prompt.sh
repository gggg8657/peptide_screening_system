#!/usr/bin/env bash
# =============================================================================
# print-harness-prompt.sh
# Codex 실행용 하네스 프롬프트를 stdout으로 조립합니다.
#
# 사용법:
#   ./scripts/codex/print-harness-prompt.sh "pipeline_local/tests 실패 수정해"
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TASK="${*:-}"

if [[ -z "${TASK// }" ]]; then
    echo "[error] task required" >&2
    exit 2
fi

cat "$ROOT/.codex/prompts/orchestrator.md"
echo
cat "$ROOT/.codex/HARNESS.md"
echo
"$SCRIPT_DIR/repo-context-for-agent.sh"
echo
cat <<EOF2
## User Task

$TASK
EOF2
