#!/usr/bin/env bash
# =============================================================================
# setup-project.sh — 프로젝트 온보딩 자동화
#
# 글로벌 Obsidian vault + Linear 동기화 + MCP + 에이전트 도구 일괄 셋업
#
# 사용법:
#   ./scripts/setup-project.sh                    # 현재 프로젝트 셋업
#   ./scripts/setup-project.sh <name> <path>      # 지정 프로젝트 셋업
#
# 최초 1회: GLOBAL_VAULT 생성 + Obsidian Linear Plugin 안내
# 프로젝트별: symlink + .linear.json + MCP + CLAUDE.md + 도구 스크립트
# =============================================================================

set -euo pipefail

# ─── 설정 ───
GLOBAL_VAULT="$HOME/Documents/ObsidianVault"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 인자 파싱
if [ $# -ge 2 ]; then
    PROJECT_NAME="$1"
    PROJECT_PATH="$(realpath "$2")"
elif [ $# -eq 1 ]; then
    PROJECT_NAME="$1"
    PROJECT_PATH="$(pwd)"
else
    PROJECT_NAME="$(basename "$(pwd)")"
    PROJECT_PATH="$(pwd)"
fi

echo "═══════════════════════════════════════════"
echo "  프로젝트 온보딩: $PROJECT_NAME"
echo "  경로: $PROJECT_PATH"
echo "  Vault: $GLOBAL_VAULT"
echo "═══════════════════════════════════════════"
echo ""

# ─── 1. 글로벌 vault 생성 ───
echo "[1/8] 글로벌 Obsidian vault 확인..."
if [ -d "$GLOBAL_VAULT" ]; then
    echo "  → 이미 존재: $GLOBAL_VAULT"
else
    mkdir -p "$GLOBAL_VAULT/.obsidian/plugins"
    mkdir -p "$GLOBAL_VAULT/Shared"
    cat > "$GLOBAL_VAULT/Shared/README.md" << 'HEREDOC'
# Shared Knowledge Base

프로젝트 간 공유 자료, 템플릿, 팀 정보를 여기에 보관합니다.
HEREDOC
    echo "  → 생성 완료: $GLOBAL_VAULT"
fi
echo ""

# ─── 2. 프로젝트 docs/ 심볼릭 링크 ───
echo "[2/8] Vault ↔ 프로젝트 심볼릭 링크..."
VAULT_PROJECT_DIR="$GLOBAL_VAULT/$PROJECT_NAME"
PROJECT_DOCS="$PROJECT_PATH/docs"

# docs/ 없으면 생성
mkdir -p "$PROJECT_DOCS"

if [ -L "$VAULT_PROJECT_DIR" ]; then
    echo "  → 이미 링크됨: $VAULT_PROJECT_DIR → $(readlink "$VAULT_PROJECT_DIR")"
elif [ -d "$VAULT_PROJECT_DIR" ]; then
    echo "  → 경고: $VAULT_PROJECT_DIR 가 이미 디렉토리로 존재. 스킵."
else
    ln -s "$PROJECT_DOCS" "$VAULT_PROJECT_DIR"
    echo "  → 링크 생성: $VAULT_PROJECT_DIR → $PROJECT_DOCS"
fi
echo ""

# ─── 3. .linear.json (프로젝트별 Linear 필터) ───
echo "[3/8] Linear 동기화 설정..."
LINEAR_CONFIG="$PROJECT_DOCS/.linear.json"
if [ -f "$LINEAR_CONFIG" ]; then
    echo "  → 이미 존재: $LINEAR_CONFIG"
else
    cat > "$LINEAR_CONFIG" << HEREDOC
{
  "team": "",
  "project": "$PROJECT_NAME",
  "syncFolder": "Linear Issues",
  "autoSync": true,
  "syncInterval": 15,
  "conflictStrategy": "manual",
  "template": "## {{title}}\\n\\n**Status**: {{status}} | **Assignee**: {{assignee}} | **Priority**: {{priority}}\\n**Linear**: [{{identifier}}]({{url}})\\n\\n---\\n\\n",
  "labels": [],
  "statusEmoji": {
    "Backlog": "📋",
    "Todo": "📝",
    "In Progress": "🔄",
    "In Review": "👀",
    "Done": "✅",
    "Cancelled": "❌"
  }
}
HEREDOC
    echo "  → 생성: $LINEAR_CONFIG"
    echo "  → Linear API 키와 팀 설정은 Obsidian 플러그인에서 직접 설정 필요"
fi
echo ""

# ─── 4. MCP 설정 (Claude Code) ───
echo "[4/8] Claude Code MCP 설정..."
MCP_FILE="$PROJECT_PATH/.mcp.json"
if [ -f "$MCP_FILE" ]; then
    echo "  → 이미 존재: $MCP_FILE"
    python3 -c "
import json
with open('$MCP_FILE') as f:
    d = json.load(f)
servers = d.get('mcpServers', {})
print(f'  → 서버 {len(servers)}개: {list(servers.keys())}')
"
else
    cat > "$MCP_FILE" << HEREDOC
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github@latest"],
      "env": {}
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem@latest", "$PROJECT_PATH"],
      "env": {}
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory@latest"],
      "env": {}
    }
  }
}
HEREDOC
    echo "  → 생성: $MCP_FILE (github + filesystem + memory)"
fi
echo ""

# ─── 5. Codex MCP 동기화 ───
echo "[5/8] Codex MCP 동기화..."
if command -v codex &>/dev/null; then
    EXISTING=$(codex mcp list 2>/dev/null | grep -c "filesystem\|github\|memory" || true)
    if [ "$EXISTING" -ge 3 ]; then
        echo "  → 이미 설정됨 ($EXISTING개 서버)"
    else
        codex mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem@latest "$PROJECT_PATH" 2>/dev/null || true
        codex mcp add github -- npx -y @modelcontextprotocol/server-github@latest 2>/dev/null || true
        codex mcp add memory -- npx -y @modelcontextprotocol/server-memory@latest 2>/dev/null || true
        echo "  → Codex MCP 추가 완료"
    fi
else
    echo "  → codex 미설치. 스킵."
fi
echo ""

# ─── 6. CLAUDE.md 배치 ───
echo "[6/8] CLAUDE.md 확인..."
CLAUDE_MD="$PROJECT_PATH/CLAUDE.md"
if [ -f "$CLAUDE_MD" ]; then
    echo "  → 이미 존재: $CLAUDE_MD"
else
    cat > "$CLAUDE_MD" << 'HEREDOC'
# CLAUDE.md

## 작업 위임 의사결정 트리

1순위: tmux team-mate (/team) — 토론, 리뷰, 실시간 모니터링
2순위: 외부 에이전트 (codex: 코드 구현, cursor-agent: 분석/일정)
3순위: 내장 서브에이전트 (Agent tool) — 복잡한 구현
4순위: 직접 구현 — 간단한 수정

## 위임 시 필수
- 요청/결과 CLI 출력
- logs/external_agents/ 로그 기록
HEREDOC
    echo "  → 생성: $CLAUDE_MD"
fi
echo ""

# ─── 7. 에이전트 도구 스크립트 ───
echo "[7/8] 에이전트 도구 스크립트 확인..."
SCRIPTS_DIR="$PROJECT_PATH/scripts"
mkdir -p "$SCRIPTS_DIR"

for script in agent-wrapper.sh watch-teammates.sh launch_agent_team.sh; do
    if [ -f "$SCRIPTS_DIR/$script" ]; then
        echo "  → 존재: $script"
    else
        echo "  → 미존재: $script (템플릿에서 복사 필요)"
    fi
done
echo ""

# ─── 8. .gitignore 업데이트 ───
echo "[8/8] .gitignore 업데이트..."
GITIGNORE="$PROJECT_PATH/.gitignore"
touch "$GITIGNORE"

ENTRIES=(
    ".obsidian/"
    "logs/external_agents/"
    "config/cache/"
    "config/secret_key"
    "config/codex.sqlite3*"
    "*.pdf"
    "local_models/gnina/gnina"
)

for entry in "${ENTRIES[@]}"; do
    if ! grep -qF "$entry" "$GITIGNORE" 2>/dev/null; then
        echo "$entry" >> "$GITIGNORE"
        echo "  → 추가: $entry"
    fi
done
echo "  → .gitignore 업데이트 완료"

echo ""
echo "═══════════════════════════════════════════"
echo "  셋업 완료!"
echo ""
echo "  Vault: $GLOBAL_VAULT/$PROJECT_NAME → $PROJECT_DOCS"
echo ""
echo "  다음 단계 (수동):"
echo "  1. Obsidian 설치: https://obsidian.md/download"
echo "  2. Vault 열기: $GLOBAL_VAULT"
echo "  3. Linear Integration 플러그인 설치"
echo "  4. Linear API 키 설정 (Settings → Linear Integration)"
echo "  5. .linear.json 의 team 필드 설정"
echo "═══════════════════════════════════════════"
