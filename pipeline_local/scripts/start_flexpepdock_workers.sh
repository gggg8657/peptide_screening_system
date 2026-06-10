#!/usr/bin/env bash
# start_flexpepdock_workers.sh
# ============================================================
# FlexPepDock Worker Pool 기동 스크립트 (4개 worker 동시 가동)
#
# 사용법:
#   bash pipeline_local/scripts/start_flexpepdock_workers.sh [--workers N]
#
# 옵션:
#   --workers N   가동할 worker 수 (기본: 4, 최대: 4)
#   --stop        가동 중인 worker 전체 종료
#   --status      worker PID 상태 확인
#
# 로그 위치:
#   /tmp/flexpepdock_worker_1.log
#   /tmp/flexpepdock_worker_2.log
#   /tmp/flexpepdock_worker_3.log
#   /tmp/flexpepdock_worker_4.log
#
# PID 파일:
#   /tmp/flexpepdock_worker_1.pid
#   /tmp/flexpepdock_worker_2.pid
#   /tmp/flexpepdock_worker_3.pid
#   /tmp/flexpepdock_worker_4.pid
# ============================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKER_SCRIPT="pipeline_local/scripts/flexpepdock_worker.py"
CONDA_ENV="bio-tools"
LOG_DIR="/tmp"
PID_DIR="/tmp"
N_WORKERS=4
ACTION="start"

# ---------------------------------------------------------------------------
# 인자 파싱
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --workers)
            N_WORKERS="${2:?--workers 인자 필요}"
            shift 2
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        --status)
            ACTION="status"
            shift
            ;;
        -h|--help)
            grep '^#' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "[ERROR] 알 수 없는 옵션: $1" >&2
            exit 1
            ;;
    esac
done

if ! [[ "${N_WORKERS}" =~ ^[1-4]$ ]]; then
    echo "[ERROR] --workers는 1~4 사이 정수여야 합니다: ${N_WORKERS}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 헬퍼 함수
# ---------------------------------------------------------------------------
pid_file() { echo "${PID_DIR}/flexpepdock_worker_${1}.pid"; }
log_file()  { echo "${LOG_DIR}/flexpepdock_worker_${1}.log"; }

is_running() {
    local pid_path
    pid_path="$(pid_file "$1")"
    if [[ ! -f "${pid_path}" ]]; then return 1; fi
    local pid
    pid="$(cat "${pid_path}")"
    if kill -0 "${pid}" 2>/dev/null; then return 0; fi
    return 1
}

# ---------------------------------------------------------------------------
# stop 액션
# ---------------------------------------------------------------------------
stop_workers() {
    echo "[INFO] FlexPepDock worker 전체 종료 요청..."
    local stopped=0
    for i in $(seq 1 "${N_WORKERS}"); do
        local pid_path
        pid_path="$(pid_file "${i}")"
        if [[ ! -f "${pid_path}" ]]; then
            echo "  [worker-${i}] PID 파일 없음 — 건너뜀"
            continue
        fi
        local pid
        pid="$(cat "${pid_path}")"
        if kill -0 "${pid}" 2>/dev/null; then
            kill -SIGTERM "${pid}" && echo "  [worker-${i}] SIGTERM 전송 (PID=${pid})"
            stopped=$((stopped + 1))
        else
            echo "  [worker-${i}] 이미 종료됨 (PID=${pid})"
        fi
        rm -f "${pid_path}"
    done
    echo "[INFO] ${stopped}개 worker 종료 요청 완료"
}

# ---------------------------------------------------------------------------
# status 액션
# ---------------------------------------------------------------------------
show_status() {
    echo "[INFO] FlexPepDock worker 상태:"
    for i in $(seq 1 4); do
        local pid_path
        pid_path="$(pid_file "${i}")"
        if [[ ! -f "${pid_path}" ]]; then continue; fi
        local pid
        pid="$(cat "${pid_path}")"
        if kill -0 "${pid}" 2>/dev/null; then
            echo "  [worker-${i}] 실행 중 (PID=${pid}) — 로그: $(log_file "${i}")"
        else
            echo "  [worker-${i}] 종료됨 (PID=${pid}, stale PID 파일)"
        fi
    done
}

# ---------------------------------------------------------------------------
# start 액션
# ---------------------------------------------------------------------------
start_workers() {
    echo "[INFO] FlexPepDock worker pool ${N_WORKERS}개 기동..."
    echo "[INFO] repo: ${REPO_ROOT}"
    echo "[INFO] conda env: ${CONDA_ENV}"

    # conda 가용성 확인
    if ! command -v conda &>/dev/null; then
        echo "[ERROR] conda 명령을 찾을 수 없습니다. conda activate 후 재시도하세요." >&2
        exit 1
    fi

    local started=0
    for i in $(seq 1 "${N_WORKERS}"); do
        local wid="worker-${i}"
        local log
        log="$(log_file "${i}")"
        local pid_path
        pid_path="$(pid_file "${i}")"

        # 이미 실행 중이면 건너뜀
        if is_running "${i}"; then
            local existing_pid
            existing_pid="$(cat "${pid_path}")"
            echo "  [${wid}] 이미 실행 중 (PID=${existing_pid}) — 건너뜀"
            continue
        fi

        echo "  [${wid}] 기동 중... (log: ${log})"

        nohup conda run --no-capture-output -n "${CONDA_ENV}" \
            python "${REPO_ROOT}/${WORKER_SCRIPT}" \
            --worker-id "${wid}" \
            >> "${log}" 2>&1 &

        local new_pid=$!
        echo "${new_pid}" > "${pid_path}"
        echo "  [${wid}] 기동 완료 (PID=${new_pid})"
        started=$((started + 1))

        # 워커 간 시작 간격 (동시 PyRosetta init 방지)
        if [[ ${i} -lt ${N_WORKERS} ]]; then
            sleep 2
        fi
    done

    echo "[INFO] ${started}개 worker 신규 기동 완료"
    echo "[INFO] 로그 확인: tail -f /tmp/flexpepdock_worker_*.log"
}

# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
case "${ACTION}" in
    start)  start_workers ;;
    stop)   stop_workers  ;;
    status) show_status   ;;
esac
