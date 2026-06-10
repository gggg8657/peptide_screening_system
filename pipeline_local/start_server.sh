#!/usr/bin/env bash
# =============================================================================
# pipeline_local/start_server.sh
# LOCAL MODE 백엔드(8787) + 프론트엔드(5173) 동시 시작 스크립트
#
# 사용법:
#   cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
#   bash pipeline_local/start_server.sh
#
# 종료:
#   Ctrl+C 로 두 프로세스 모두 종료 (trap 처리됨)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 경로 상수
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${REPO_ROOT}/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend"
BACKEND_MODULE="pipeline_local.backend.main"

# ---------------------------------------------------------------------------
# 환경 변수 설정
# ---------------------------------------------------------------------------
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11435}"
export API_PORT="${API_PORT:-8787}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-2}"

# ---------------------------------------------------------------------------
# PID 파일 경로
# ---------------------------------------------------------------------------
PID_FILE="/tmp/pipeline_local_backend.pid"

# ---------------------------------------------------------------------------
# Python 경로 결정 (bio-tools conda 환경 우선)
# ---------------------------------------------------------------------------
_find_python() {
    for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3"; do
        local py="${base}/envs/bio-tools/bin/python"
        if [ -f "$py" ]; then
            echo "$py"
            return 0
        fi
    done
    echo "python3"
}
PYTHON_BIN="$(_find_python)"

# ---------------------------------------------------------------------------
# 이전 인스턴스 정리
#   1. PID 파일 존재 시 — 해당 프로세스가 살아있으면 종료 (stale 엔트리 제거)
#   2. 포트 8787이 점유 중이면 점유 프로세스 종료
# ---------------------------------------------------------------------------
_cleanup_old_instance() {
    # (1) PID 파일 기반 정리
    if [ -f "${PID_FILE}" ]; then
        local old_pid
        old_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
        if [ -n "${old_pid}" ] && kill -0 "${old_pid}" 2>/dev/null; then
            echo "[guard] 이전 백엔드 프로세스 종료 중 (pid=${old_pid})..."
            kill "${old_pid}" 2>/dev/null || true
            # 최대 5초 대기
            local i=0
            while kill -0 "${old_pid}" 2>/dev/null && [ "${i}" -lt 10 ]; do
                sleep 0.5
                i=$((i + 1))
            done
            # 여전히 살아있으면 강제 종료
            if kill -0 "${old_pid}" 2>/dev/null; then
                echo "[guard] SIGKILL 전송 (pid=${old_pid})"
                kill -9 "${old_pid}" 2>/dev/null || true
            fi
            echo "[guard] 이전 프로세스 종료 완료 (pid=${old_pid})"
        else
            echo "[guard] PID 파일 발견 (pid=${old_pid:-?}) — 프로세스 없음, stale 항목 제거"
        fi
        rm -f "${PID_FILE}"
    fi

    # (2) 포트 점유 프로세스 정리 (PID 파일에 기록되지 않은 경우 대비)
    local port_pid
    port_pid="$(lsof -ti tcp:"${API_PORT}" 2>/dev/null | head -1 || true)"
    if [ -n "${port_pid}" ]; then
        echo "[guard] 포트 ${API_PORT} 이미 사용 중 (pid=${port_pid}) — 종료 중..."
        kill "${port_pid}" 2>/dev/null || true
        sleep 1
        if kill -0 "${port_pid}" 2>/dev/null; then
            kill -9 "${port_pid}" 2>/dev/null || true
        fi
        echo "[guard] 포트 ${API_PORT} 해제 완료"
    fi
}

# ---------------------------------------------------------------------------
# 프로세스 PID 추적 (Ctrl+C 처리용)
# ---------------------------------------------------------------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "[stop] 서버 종료 중..."
    [ -n "$BACKEND_PID"  ] && kill "$BACKEND_PID"  2>/dev/null && echo "  [ok] 백엔드 종료 (pid=${BACKEND_PID})"
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && echo "  [ok] 프론트엔드 종료 (pid=${FRONTEND_PID})"
    # PID 파일 제거
    rm -f "${PID_FILE}"
    wait 2>/dev/null
    echo "[stop] 완료"
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# 이전 인스턴스 정리 실행
# ---------------------------------------------------------------------------
_cleanup_old_instance

# ---------------------------------------------------------------------------
# 백엔드 시작 (포트 8787)
# ---------------------------------------------------------------------------
echo "============================================================"
echo "  LOCAL MODE 서버 시작"
echo "  REPO_ROOT    : ${REPO_ROOT}"
echo "  OLLAMA_HOST  : ${OLLAMA_HOST}"
echo "  CUDA_DEVICES : ${CUDA_VISIBLE_DEVICES}"
echo "  Python       : ${PYTHON_BIN}"
echo "  PID 파일     : ${PID_FILE}"
echo "============================================================"
echo ""

echo "[backend] 시작 중 (port=${API_PORT})..."
cd "${REPO_ROOT}"
"${PYTHON_BIN}" -m uvicorn \
    "${BACKEND_MODULE}:app" \
    --host 0.0.0.0 \
    --port "${API_PORT}" \
    --reload \
    --reload-dir pipeline_local \
    --log-level info &
BACKEND_PID="$!"
echo "[backend] PID=${BACKEND_PID}"

# PID 파일 기록
echo "${BACKEND_PID}" > "${PID_FILE}"
echo "[backend] PID 파일 기록 -> ${PID_FILE}"

# 백엔드가 준비될 때까지 잠시 대기
sleep 2

# ---------------------------------------------------------------------------
# 프론트엔드 시작 (포트 5173)
# ---------------------------------------------------------------------------
if [ -d "${FRONTEND_DIR}" ] && [ -f "${FRONTEND_DIR}/package.json" ]; then
    echo "[frontend] 시작 중 (port=5173)..."
    cd "${FRONTEND_DIR}"
    npm run dev -- --port 5173 &
    FRONTEND_PID="$!"
    echo "[frontend] PID=${FRONTEND_PID}"
    cd "${REPO_ROOT}"
else
    echo "[frontend] 디렉토리 없음: ${FRONTEND_DIR}"
    echo "[frontend] 백엔드만 실행됩니다."
fi

echo ""
echo "============================================================"
echo "  서버 실행 중"
echo "  Backend  : http://localhost:${API_PORT}/api/health"
echo "  Frontend : http://localhost:5173"
echo "  Ctrl+C 로 종료"
echo "============================================================"
echo ""

# 두 프로세스 중 하나가 종료될 때까지 대기
wait
