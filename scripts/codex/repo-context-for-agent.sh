#!/usr/bin/env bash
# =============================================================================
# repo-context-for-agent.sh
# Codex 프롬프트/메모에 붙여넣기 좋은 레포 스냅샷을 stdout으로 출력합니다.
#
# 사용법:
#   ./scripts/codex/repo-context-for-agent.sh
#   ./scripts/codex/repo-context-for-agent.sh --json
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
JSON=0
[[ "${1:-}" == "--json" ]] && JSON=1

cd "$ROOT"

branch=$(git branch --show-current 2>/dev/null || echo "(not a git repo)")
describe=$(git describe --always --dirty 2>/dev/null || true)

if [[ "$JSON" -eq 1 ]]; then
    export _CODEX_CTX_ROOT="$ROOT" _CODEX_CTX_BRANCH="$branch" _CODEX_CTX_DESCRIBE="$describe"
    python3 - <<'PY'
import json, os, subprocess

root = os.environ["_CODEX_CTX_ROOT"]
branch = os.environ["_CODEX_CTX_BRANCH"]
describe = os.environ["_CODEX_CTX_DESCRIBE"]

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, cwd=root).strip()
    except subprocess.CalledProcessError:
        return ""

obj = {
    "repo_root": root,
    "git_branch": branch,
    "git_describe": describe,
    "status_short": run("git status -sb"),
    "log_recent": run("git log -5 --oneline"),
}
print(json.dumps(obj, indent=2, ensure_ascii=False))
PY
    exit 0
fi

cat <<EOF2
## Repo context (for Codex)

- **ROOT**: \`$ROOT\`
- **Branch**: \`$branch\`
- **Describe**: \`$describe\`
- **Date (host)**: $(date -Iseconds)

### git status (-sb)

\`\`\`
$(git status -sb 2>/dev/null || echo "(git unavailable)")
\`\`\`

### Recent commits

\`\`\`
$(git log -5 --oneline 2>/dev/null || echo "(git unavailable)")
\`\`\`
EOF2

if [[ -f "$ROOT/ENVIRONMENT.md" ]]; then
    echo ""
    echo "### ENVIRONMENT.md (head)"
    echo ""
    echo '```'
    head -n 40 "$ROOT/ENVIRONMENT.md"
    echo '```'
fi

if command -v conda &>/dev/null; then
    echo ""
    echo "### conda (active env 이름만)"
    echo ""
    echo '```'
    echo "${CONDA_DEFAULT_ENV:-"(none)"}"
    echo '```'
fi
