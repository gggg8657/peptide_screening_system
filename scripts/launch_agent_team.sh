#!/usr/bin/env bash
# =============================================================================
# launch_agent_team.sh
# tmux 기반 에이전트 팀 런처
#
# 오케스트레이터 1명 + 팀원 5명이 각자 tmux pane에서 실행됩니다.
#
# 사용법:
#   ./scripts/launch_agent_team.sh [task_description]
#   ./scripts/launch_agent_team.sh "UI/UX Phase 1 Critical 수정"
#   ./scripts/launch_agent_team.sh  # (기본: 대화형 오케스트레이터)
# =============================================================================

set -euo pipefail

SESSION="agent-team"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK="${1:-}"

# 기존 세션 있으면 확인
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "[WARN] '$SESSION' 세션이 이미 존재합니다."
    echo "  접속: tmux attach -t $SESSION"
    echo "  종료: tmux kill-session -t $SESSION"
    read -p "기존 세션 종료 후 새로 시작? (y/N): " yn
    case $yn in
        [Yy]* ) tmux kill-session -t "$SESSION" ;;
        * ) echo "기존 세션에 접속합니다."; tmux attach -t "$SESSION"; exit 0 ;;
    esac
fi

cd "$PROJECT_DIR"

# =============================================================================
# 팀 구성: 6 agents (orchestrator + 5 teammates)
# =============================================================================

# CLAUDECODE 환경변수 제거 — 부모 Claude Code 세션에서 실행 시 중첩 방지 해제
C="env -u CLAUDECODE -u CLAUDE_CODE claude"

# 세션 생성 — 오케스트레이터 (메인 pane)
if [ -n "$TASK" ]; then
    tmux new-session -d -s "$SESSION" -n "team" \
        "$C --agent orchestrator --permission-mode auto -p '다음 작업을 팀에 분장하고 진행하세요: $TASK' ; bash"
else
    tmux new-session -d -s "$SESSION" -n "team" \
        "$C --agent orchestrator --permission-mode auto ; bash"
fi

# 팀원 1: 코드 리뷰어
tmux split-window -t "$SESSION:team" -h \
    "$C --agent reviewer-code --permission-mode auto ; bash"

# 팀원 2: 과학 리뷰어
tmux split-window -t "$SESSION:team" -v \
    "$C --agent reviewer-science --permission-mode auto ; bash"

# 팀원 3: 백엔드 엔지니어
tmux select-pane -t "$SESSION:team.0"
tmux split-window -t "$SESSION:team" -v \
    "$C --agent engineer-backend --permission-mode auto ; bash"

# 팀원 4: 인프라 엔지니어 (새 윈도우)
tmux new-window -t "$SESSION" -n "infra" \
    "$C --agent engineer-infra --permission-mode auto ; bash"

# 팀원 5: UI/UX 리뷰어 (새 윈도우)
tmux new-window -t "$SESSION" -n "uiux" \
    "$C --agent reviewer-uiux --permission-mode auto ; bash"

# 레이아웃 정리
tmux select-window -t "$SESSION:team"
tmux select-layout -t "$SESSION:team" tiled

# 상태 표시
tmux set -t "$SESSION" status-left "#[bg=blue,fg=white] AGENT-TEAM "
tmux set -t "$SESSION" status-right "#[bg=green,fg=black] 오케스트레이터+5팀원 "

echo "=============================================="
echo " Agent Team 시작됨!"
echo ""
echo " 세션: $SESSION"
echo " 윈도우 1 (team): orchestrator + reviewer-code + reviewer-science + engineer-backend"
echo " 윈도우 2 (infra): engineer-infra"
echo " 윈도우 3 (uiux): reviewer-uiux"
echo ""
echo " 접속: tmux attach -t $SESSION"
echo " 종료: tmux kill-session -t $SESSION"
echo "=============================================="

# 자동 접속
tmux attach -t "$SESSION"
