#!/usr/bin/env bash
# =============================================================================
# auto-dispatch-preview.sh
# 상위 스크립트 auto_dispatch.sh 의 --dry-run 단축 래퍼.
# Cursor 안에서 라우팅만 확인하고 실제 CLI는 돌리지 않을 때 사용.
#
# 사용법:
#   ./scripts/cursor/auto-dispatch-preview.sh "backend/foo.py 코드 리뷰해줘"
#   ./scripts/cursor/auto-dispatch-preview.sh --topic my-topic "분석해 …"
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/../auto_dispatch.sh" --dry-run "$@"
