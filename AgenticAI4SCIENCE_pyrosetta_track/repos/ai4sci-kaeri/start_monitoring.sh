#!/usr/bin/env bash
# =============================================================================
# SSTR2 Pipeline + Monitoring Dashboard Launcher
# =============================================================================
# Launches three processes in parallel:
#   1. Backend API server  (port 8787)
#   2. Frontend dev server (port 5173, proxies /api → 8787)
#   3. Pipeline execution  (run_pipeline_live.py)
#
# Usage:
#   chmod +x start_monitoring.sh
#   ./start_monitoring.sh
#
# Requirements:
#   - NVIDIA_NIM_API_KEY environment variable (or loads from .env)
#   - Node.js + npm (for frontend)
#   - Python 3.10+ (for backend + pipeline)
# =============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Colors
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
BOLD='\033[1m'
RESET='\033[0m'

log() { echo -e "${CYAN}[launcher]${RESET} $1"; }
ok()  { echo -e "${GREEN}[launcher] ✓${RESET} $1"; }
err() { echo -e "${RED}[launcher] ✗${RESET} $1"; }

# ── Load API key from .env if not set ──
if [ -z "${NVIDIA_NIM_API_KEY:-}" ]; then
    ENV_FILE="$ROOT_DIR/PRST_N_FM/bionemo/.env"
    if [ -f "$ENV_FILE" ]; then
        # Source .env - handles NGC_CLI_API_KEY or NVIDIA_NIM_API_KEY
        set -a
        source "$ENV_FILE"
        set +a
        # Map NGC_CLI_API_KEY → NVIDIA_NIM_API_KEY if needed
        if [ -z "${NVIDIA_NIM_API_KEY:-}" ] && [ -n "${NGC_CLI_API_KEY:-}" ]; then
            export NVIDIA_NIM_API_KEY="$NGC_CLI_API_KEY"
        fi
        ok "API key loaded from $ENV_FILE"
    else
        err "NVIDIA_NIM_API_KEY not set and no .env file found"
        exit 1
    fi
fi

# ── Check prerequisites ──
log "Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    err "python3 not found"; exit 1
fi

if ! command -v node &>/dev/null; then
    err "node not found"; exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    log "Installing frontend dependencies..."
    (cd "$ROOT_DIR/frontend" && npm install)
fi

ok "Prerequisites OK"

# ── Cleanup handler ──
PIDS=()
cleanup() {
    log "Shutting down all processes..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    # Clean up status file
    rm -f /tmp/pipeline_local_status.json  # 2026-05-14: status_emitter writer 통일 (P01)
    ok "All processes stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# ── 1. Start Backend API Server ──
log "${BOLD}Starting backend API server (port 8787)...${RESET}"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8787 &
PIDS+=($!)
sleep 1

# Verify backend is running
if curl -s http://localhost:8787/api/health > /dev/null 2>&1; then
    ok "Backend API server running on http://localhost:8787"
else
    err "Backend API server failed to start"
    exit 1
fi

# ── 2. Start Frontend Dev Server ──
log "${BOLD}Starting frontend dev server (port 5173)...${RESET}"
(cd "$ROOT_DIR/frontend" && npm run dev -- --host 2>&1 | while IFS= read -r line; do
    echo -e "${YELLOW}[frontend]${RESET} $line"
done) &
PIDS+=($!)
sleep 3
ok "Frontend dev server starting on http://localhost:5173"

# ── 3. Run Pipeline ──
log "${BOLD}Starting pipeline execution...${RESET}"
echo ""
echo -e "${BOLD}${GREEN}================================================${RESET}"
echo -e "${BOLD}${GREEN}  Dashboard: http://localhost:5173${RESET}"
echo -e "${BOLD}${GREEN}  API:       http://localhost:8787/api/status${RESET}"
echo -e "${BOLD}${GREEN}================================================${RESET}"
echo ""
echo -e "${CYAN}Open the dashboard in your browser to monitor the pipeline in real-time.${RESET}"
echo ""

# Small delay to let frontend start fully
sleep 2

python3 "$ROOT_DIR/run_pipeline_live.py" 2>&1 | while IFS= read -r line; do
    echo "$line"
done
PIPELINE_EXIT=$?

if [ $PIPELINE_EXIT -eq 0 ]; then
    ok "Pipeline completed successfully!"
else
    err "Pipeline exited with code $PIPELINE_EXIT"
fi

# Keep servers running for 60s after pipeline completes so user can review dashboard
echo ""
log "Pipeline finished. Dashboard remains live for review."
log "Press Ctrl+C to stop all services."
echo ""

# Wait indefinitely until user interrupts
wait
