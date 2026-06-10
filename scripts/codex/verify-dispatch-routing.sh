#!/usr/bin/env bash
# =============================================================================
# verify-dispatch-routing.sh
# harness 라우팅 회귀: ../test_auto_dispatch_routing.sh 를 호출합니다.
#
# 사용법:
#   ./scripts/codex/verify-dispatch-routing.sh
#   ./scripts/codex/verify-dispatch-routing.sh --quiet
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/../test_auto_dispatch_routing.sh" "$@"
