#!/usr/bin/env bash
# ============================================================
#  PRST_N_FM Demo Launcher
#  터미널에서 실행: bash docs/run_demo.sh
#  → Backend (FastAPI :8787) + Frontend (Vite :5173) 자동 기동
#  → http://localhost:5173 접속하여 데모 진행
# ============================================================
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri"
BACKEND="$APP/backend"
FRONTEND="$APP/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

cleanup() {
  echo ""
  echo -e "${YELLOW}[DEMO] Shutting down...${NC}"
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "  Backend (PID $BACKEND_PID) stopped"
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && echo "  Frontend (PID $FRONTEND_PID) stopped"
  exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   PRST_N_FM  —  SSTR2 Peptide Screening     ║${NC}"
echo -e "${CYAN}║         Demo Launcher v1.0                   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Check Python + pip ──
echo -e "${GREEN}[1/4]${NC} Checking Python environment..."
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}ERROR: python3 not found. Install Python 3.10+${NC}"
  exit 1
fi

# ── 2. Install backend deps ──
echo -e "${GREEN}[2/4]${NC} Installing backend dependencies..."
pip3 install -q fastapi uvicorn pydantic requests 2>/dev/null || \
  pip install -q fastapi uvicorn pydantic requests 2>/dev/null || true

# ── 3. Install frontend deps ──
echo -e "${GREEN}[3/4]${NC} Checking frontend dependencies..."
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "  Installing npm packages..."
  cd "$FRONTEND" && npm install --silent
  cd "$ROOT"
else
  echo "  node_modules OK"
fi

# ── 4. Launch servers ──
echo -e "${GREEN}[4/4]${NC} Starting servers..."
echo ""

# Backend
echo -e "  ${CYAN}Backend${NC}  → http://localhost:8787"
cd "$APP"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8787 --reload \
  > /tmp/prst_demo_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
for i in {1..10}; do
  if curl -s http://localhost:8787/api/health > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Frontend
echo -e "  ${CYAN}Frontend${NC} → http://localhost:5173"
cd "$FRONTEND"
npx vite --host > /tmp/prst_demo_frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend
sleep 3

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Demo Ready!                                 ║${NC}"
echo -e "${GREEN}║  Open: ${CYAN}http://localhost:5173${GREEN}                ║${NC}"
echo -e "${GREEN}║                                              ║${NC}"
echo -e "${GREEN}║  Pages:                                      ║${NC}"
echo -e "${GREEN}║    /silo-b   Silo B (PyRosetta)              ║${NC}"
echo -e "${GREEN}║    /silo-a   Silo A (NIM API)                ║${NC}"
echo -e "${GREEN}║    /settings Settings                        ║${NC}"
echo -e "${GREEN}║    /about    About                           ║${NC}"
echo -e "${GREEN}║                                              ║${NC}"
echo -e "${GREEN}║  Press ${YELLOW}Ctrl+C${GREEN} to stop                       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# macOS: auto-open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
  open "http://localhost:5173/silo-b" 2>/dev/null || true
fi

# Logs
echo -e "${YELLOW}[LOG]${NC} Backend:  tail -f /tmp/prst_demo_backend.log"
echo -e "${YELLOW}[LOG]${NC} Frontend: tail -f /tmp/prst_demo_frontend.log"
echo ""

# Keep alive
wait
