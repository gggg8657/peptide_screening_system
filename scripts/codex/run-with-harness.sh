#!/usr/bin/env bash
# =============================================================================
# run-with-harness.sh
# Codex harness 프롬프트를 조립한 뒤 agent-wrapper를 통해 codex exec를 실행합니다.
#
# 사용법:
#   ./scripts/codex/run-with-harness.sh "backend 버그 수정해"
#   ./scripts/codex/run-with-harness.sh --dry-run "step05b 분석해"
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=1
    shift
fi

TASK="${*:-}"
if [[ -z "${TASK// }" ]]; then
    echo "[error] task required" >&2
    exit 2
fi

PROMPT="$($SCRIPT_DIR/print-harness-prompt.sh "$TASK")"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] ./scripts/agent-wrapper.sh codex exec <harness-prompt>"
    echo
    printf '%s\n' "$PROMPT"
    exit 0
fi

cd "$ROOT"
exec "$ROOT/scripts/agent-wrapper.sh" codex exec "$PROMPT"
