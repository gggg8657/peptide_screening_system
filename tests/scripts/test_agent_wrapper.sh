#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WRAPPER="$ROOT_DIR/scripts/agent-wrapper.sh"
LOG_DIR="$ROOT_DIR/logs/external_agents"

fail() {
    echo "[FAIL] $*" >&2
    exit 1
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    if [[ "$haystack" != *"$needle"* ]]; then
        fail "expected to find: $needle"
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    if [[ "$haystack" == *"$needle"* ]]; then
        fail "did not expect to find: $needle"
    fi
}

TMP_DIR="$(mktemp -d)"
FAKE_BIN="$TMP_DIR/bin"
mkdir -p "$FAKE_BIN" "$LOG_DIR"

cleanup() {
    rm -rf "$TMP_DIR"
    if [[ -f "$TMP_DIR/history.restore" ]]; then
        cp "$TMP_DIR/history.restore" "$LOG_DIR/history.jsonl"
    else
        rm -f "$LOG_DIR/history.jsonl"
    fi
    if [[ -f "$TMP_DIR/logs.before" ]]; then
        while IFS= read -r path; do
            [[ -n "$path" ]] || continue
            rm -f "$path"
        done < <(comm -13 "$TMP_DIR/logs.before" "$TMP_DIR/logs.after")
    fi
}
trap cleanup EXIT

if [[ -f "$LOG_DIR/history.jsonl" ]]; then
    cp "$LOG_DIR/history.jsonl" "$TMP_DIR/history.restore"
fi

find "$LOG_DIR" -maxdepth 1 -type f | sort > "$TMP_DIR/logs.before"

cat > "$FAKE_BIN/codex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "argv:$#"
idx=1
for arg in "$@"; do
    printf 'arg%d=<%s>\n' "$idx" "$arg"
    idx=$((idx + 1))
done
if IFS= read -r line; then
    printf 'stdin=<%s>\n' "$line"
else
    echo 'stdin=<EOF>'
fi
EOF

cat > "$FAKE_BIN/cursor-agent" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "argv:$#"
idx=1
for arg in "$@"; do
    printf 'arg%d=<%s>\n' "$idx" "$arg"
    idx=$((idx + 1))
done
if IFS= read -r line; then
    printf 'stdin=<%s>\n' "$line"
else
    echo 'stdin=<EOF>'
fi
EOF

cat > "$FAKE_BIN/mock-agent" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "argv:$#"
idx=1
for arg in "$@"; do
    printf 'arg%d=<%s>\n' "$idx" "$arg"
    idx=$((idx + 1))
done
if IFS= read -r line; then
    printf 'stdin=<%s>\n' "$line"
else
    echo 'stdin=<EOF>'
fi
EOF

chmod +x "$FAKE_BIN/codex" "$FAKE_BIN/cursor-agent" "$FAKE_BIN/mock-agent"

export PATH="$FAKE_BIN:$PATH"

cursor_output="$(printf 'payload\n' | "$WRAPPER" cursor-agent -p 'curl -s https://example.com')"
assert_contains "$cursor_output" 'arg1=<-p>'
assert_contains "$cursor_output" 'arg2=<curl -s https://example.com>'
assert_contains "$cursor_output" 'stdin=<EOF>'
assert_not_contains "$cursor_output" 'stdin=<payload>'

codex_exec_output="$(printf 'payload\n' | "$WRAPPER" codex exec 'curl -s https://example.com')"
assert_contains "$codex_exec_output" 'arg1=<exec>'
assert_contains "$codex_exec_output" 'arg2=<--dangerously-bypass-approvals-and-sandbox>'
assert_contains "$codex_exec_output" 'arg3=<curl -s https://example.com>'
assert_contains "$codex_exec_output" 'stdin=<EOF>'

codex_review_output="$(printf 'payload\n' | "$WRAPPER" codex review)"
assert_contains "$codex_review_output" 'arg1=<review>'
assert_contains "$codex_review_output" 'stdin=<EOF>'

generic_output="$(printf 'payload\n' | "$WRAPPER" mock-agent alpha 'beta gamma')"
assert_contains "$generic_output" 'arg1=<alpha>'
assert_contains "$generic_output" 'arg2=<beta gamma>'
assert_contains "$generic_output" 'stdin=<EOF>'

find "$LOG_DIR" -maxdepth 1 -type f | sort > "$TMP_DIR/logs.after"
new_logs_count="$(comm -13 "$TMP_DIR/logs.before" "$TMP_DIR/logs.after" | wc -l | tr -d ' ')"
[[ "$new_logs_count" -ge 3 ]] || fail "expected new wrapper logs to be created"

history_tail="$(tail -n 4 "$LOG_DIR/history.jsonl")"
assert_contains "$history_tail" '"agent": "cursor-agent"'
assert_contains "$history_tail" '"agent": "codex"'
assert_contains "$history_tail" '"agent": "mock-agent"'

echo "[PASS] agent-wrapper args and stdin handling verified"
