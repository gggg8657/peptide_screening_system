#!/usr/bin/env bash
# =============================================================================
# run_with_status.sh — CLI ad-hoc 실험용 STATUS_FILE 자동 갱신 래퍼
# =============================================================================
#
# Usage:
#   bash scripts/run_with_status.sh <task_name> <python_or_any_command> [args...]
#
# Examples:
#   bash scripts/run_with_status.sh "step08_stability" \
#       python pipeline_local/steps/step08_stability.py --seq-id cand01
#
#   bash scripts/run_with_status.sh "dogfood_test" sleep 5
#
#   bash scripts/run_with_status.sh "stability_predictor" \
#       python -m pipeline_local.scripts.stability_predictor \
#       --sequences AGCKNFFWKTFTSC --seq-ids ref
#
# 환경변수:
#   PIPELINE_STATUS_FILE  기본: /tmp/pipeline_local_status.json
#   PIPELINE_EVENTS_JSONL 기본: /tmp/pipeline_events.jsonl
#   CONDA_ENV             conda 환경 이름 (미설정 시 현재 환경)
#
# 동작:
#   1. status_updater.py --start <task_name> 호출 → STATUS_FILE 갱신
#   2. 원본 커맨드 실행
#   3. status_updater.py --end <task_name> --exit-code $? 호출 → 완료 기록
#   4. 원본 종료 코드로 exit
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 인자 파싱
# ---------------------------------------------------------------------------
if [[ $# -lt 2 ]]; then
    echo "Usage: bash run_with_status.sh <task_name> <command> [args...]" >&2
    echo "  task_name: STATUS_FILE에 기록될 작업명" >&2
    exit 1
fi

TASK_NAME="$1"
shift  # 나머지는 실행할 커맨드

# ---------------------------------------------------------------------------
# 환경 설정
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PIPELINE_STATUS_FILE="${PIPELINE_STATUS_FILE:-/tmp/pipeline_local_status.json}"
export PIPELINE_EVENTS_JSONL="${PIPELINE_EVENTS_JSONL:-/tmp/pipeline_events.jsonl}"

UPDATER="$REPO_ROOT/pipeline_local/scripts/status_updater.py"

# status_updater.py 존재 확인
if [[ ! -f "$UPDATER" ]]; then
    echo "[run_with_status] ⚠️  status_updater.py 없음: $UPDATER" >&2
    echo "[run_with_status] STATUS_FILE 갱신 없이 커맨드를 직접 실행합니다." >&2
    exec "$@"
fi

# conda 환경 내 python 선택
if [[ -n "${CONDA_ENV:-}" ]]; then
    PYTHON="conda run -n $CONDA_ENV python"
else
    PYTHON="python"
fi

# ---------------------------------------------------------------------------
# START 기록
# ---------------------------------------------------------------------------
echo "[run_with_status] ▶ task='$TASK_NAME' 시작"
$PYTHON "$UPDATER" --start "$TASK_NAME" 2>/dev/null || \
    echo "[run_with_status] ⚠️  STATUS_FILE start 기록 실패 (계속 진행)"

# ---------------------------------------------------------------------------
# 원본 커맨드 실행
# ---------------------------------------------------------------------------
EXIT_CODE=0
"$@" || EXIT_CODE=$?

# ---------------------------------------------------------------------------
# END 기록
# ---------------------------------------------------------------------------
$PYTHON "$UPDATER" --end "$TASK_NAME" --exit-code "$EXIT_CODE" 2>/dev/null || \
    echo "[run_with_status] ⚠️  STATUS_FILE end 기록 실패"

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "[run_with_status] ✅ task='$TASK_NAME' 완료"
else
    echo "[run_with_status] ❌ task='$TASK_NAME' 실패 (exit=$EXIT_CODE)"
fi

exit $EXIT_CODE
