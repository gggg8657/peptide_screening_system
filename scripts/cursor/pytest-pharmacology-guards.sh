#!/usr/bin/env bash
# =============================================================================
# pytest-pharmacology-guards.sh
# Stage 5 약리 가드 관련 빠른 회귀 (Cursor에서 수정 검증용).
#
# 사용법:
#   ./scripts/cursor/pytest-pharmacology-guards.sh
#   CONDA_ENV=bio-tools ./scripts/cursor/pytest-pharmacology-guards.sh
#
# NOTE: 레포별 conda 이름은 ENVIRONMENT.md / 로컬 관례를 따르세요.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

PY=(python3 -m pytest)
if [[ -n "${CONDA_ENV:-}" ]]; then
    PY=(conda run -n "$CONDA_ENV" python -m pytest)
fi

exec "${PY[@]}" -q pipeline_local/tests/test_pharmacology_guards.py "$@"
