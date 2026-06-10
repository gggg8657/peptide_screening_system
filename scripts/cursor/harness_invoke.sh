#!/usr/bin/env bash
# =============================================================================
# harness_invoke.sh — Cursor CLI harness (실행형)
#
# 레포 신규: tools/harness-adaptation/cursor-cli/stages/*.md 단계별 프롬프트 조합 후
# scripts/agent-wrapper.sh cursor-agent 호출만 수행 (agent-wrapper 내용 미수정).
#
# 사용법:
#   ./scripts/cursor/harness_invoke.sh list
#   ./scripts/cursor/harness_invoke.sh run explore --topic myfeat --task "상태 API 조사"
#   ./scripts/cursor/harness_invoke.sh run explore ... --dry-run|--execute
#                       (기본: --dry-run, 실제 실행은 --execute 필요)
#   ./scripts/cursor/harness_invoke.sh chain explore,synthesize,review_gate --topic t --task "..."
#
# STAGE: stages/*.md stem (예: 01_explore) 또는 YAML frontmatter stage_id (예: explore)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARNESS_CLI_ROOT="${HARNESS_CLI_ROOT:-$REPO_ROOT/tools/harness-adaptation/cursor-cli}"
STAGES_DIR="$HARNESS_CLI_ROOT/stages"
WRAPPER="$REPO_ROOT/scripts/agent-wrapper.sh"

DRY_RUN=1
TASK=""
TOPIC_SLUG=""
MODE=""
BATCH_NN_BASE=""
BATCH_STAGE_INDEX=""
PREV_OUTPUT=""

usage() {
    sed -n '3,20p' "$0"
}

next_workspace_max_plus_one() {
    local d="$REPO_ROOT/_workspace"
    mkdir -p "$d"
    python3 -c "
import pathlib, sys
base = pathlib.Path(sys.argv[1])
mx = -1
if base.exists():
    for p in base.iterdir():
        n = p.name
        if len(n)>=3 and n[0].isdigit() and n[1].isdigit() and n[2]=='_':
            try:
                v = int(n[:2])
                mx = max(mx, v)
            except ValueError:
                pass
sys.stdout.write('%02d' % (mx + 1))
" "$d"
}

slug_ascii() {
    local s="$1"
    printf '%s' "$s" | head -c 80 \
        | LC_ALL=C tr '[:upper:]' '[:lower:]' \
        | LC_ALL=C tr -c 'a-z0-9' '-' \
        | LC_ALL=C sed -E 's/-+/-/g; s/^-+|-+$//g' \
        | head -c 24
}

expand_stage_md() {
    HMD="$1" HOUT="${2:?}" HPREV="${3:-}" \
        HROOT="$REPO_ROOT" HTOPIC="${TOPIC_SLUG:-topic}" HTASK="${TASK:-}" \
        python3 <<'PYCODE'
import os
import pathlib
import sys

md = pathlib.Path(os.environ["HMD"]).resolve()
PROJECT_ROOT = os.environ["HROOT"]
TOPIC = os.environ["HTOPIC"] or "topic"
OUT = os.environ["HOUT"]
PREV = os.environ.get("HPREV", "")
TASK_TEXT = os.environ.get("HTASK", "")

text = md.read_text(encoding="utf-8")
body = text
if body.startswith("---"):
    end = body.find("\n---", 4)
    if end != -1:
        body = body[end + 4 :].lstrip("\n")

prev_empty = "(이전 단계 산출 없음; 사용자가 경로 제공)"
task_empty = "(TASK 미지정; 과제 채울 것)"
repl = {
    "{{PROJECT_ROOT}}": PROJECT_ROOT,
    "{{TOPIC_SLUG}}": TOPIC,
    "{{OUTPUT_PATH}}": OUT,
    "{{PREV_OUTPUT}}": prev_empty if not PREV.strip() else PREV,
    "{{TASK}}": task_empty if not TASK_TEXT.strip() else TASK_TEXT,
}
for k, v in repl.items():
    body = body.replace(k, v)
sys.stdout.write(body)
PYCODE
}

resolve_stage_path() {
    HTOK="$1" HROOT="$STAGES_DIR" python3 <<'PYCODE'
import os
import pathlib
import re
import sys

Tok_raw = os.environ["HTOK"].strip().lower()
ROOT = pathlib.Path(os.environ["HROOT"])
if not ROOT.is_dir():
    sys.stderr.write(f"[error] stages dir 없음: {ROOT}\n")
    sys.exit(3)


def parse_stage_id(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end != -1:
            fm = text[4:end]
            for line in fm.splitlines():
                m = re.match(r"^\s*stage_id:\s*(.+)", line.strip())
                if m:
                    raw = m.group(1).strip()
                    for ch in "\"'":
                        raw = raw.strip(ch)
                    return path, path.stem.lower(), raw.lower()
    return path, path.stem.lower(), None


cands = []
for p in sorted(ROOT.glob("*.md")):
    full, stem, sid = parse_stage_id(p)
    cands.append((full, stem, sid))

needle = Tok_raw
for path, stem, sid in cands:
    if stem == needle or (sid and sid == needle):
        print(path.resolve())
        sys.exit(0)
sys.stderr.write(
    f"[error] unknown stage token: {os.environ['HTOK']!r}. harness_invoke.sh list 참고.\n"
)
sys.exit(1)
PYCODE
}

ensure_dirs() {
    if [[ ! -d "$STAGES_DIR" ]]; then
        echo "[error] stages 디렉토리 없음: $STAGES_DIR" >&2
        exit 3
    fi
}

compute_nn_for_stage() {
    if [[ -n "${BATCH_NN_BASE}" && "${BATCH_STAGE_INDEX}" != "" ]]; then
        printf '%02d' "$((10#${BATCH_NN_BASE} + BATCH_STAGE_INDEX))"
    else
        next_workspace_max_plus_one
    fi
}

run_one_stage() {
    local token="$1"
    local md_path nn TOPIC_FINAL OUTPUT_PATH PROMPT_BODY
    md_path="$(resolve_stage_path "$token")" || exit 1
    nn="$(compute_nn_for_stage)"
    TOPIC_FINAL="${TOPIC_SLUG:-}"
    [[ -z "$TOPIC_FINAL" ]] && TOPIC_FINAL="$(slug_ascii "${token}_harness")"

    OUTPUT_PATH="$REPO_ROOT/_workspace/${nn}_cursor-${TOPIC_FINAL}_$(basename "$md_path" .md).md"
    PROMPT_BODY="$(expand_stage_md "$md_path" "$OUTPUT_PATH" "${PREV_OUTPUT}")"

    echo ""
    echo "═══════════════════════════════════════════"
    echo "  harness_invoke: stage $token"
    echo "  NN / output:  $OUTPUT_PATH"
    [[ -n "${PREV_OUTPUT}" ]] && echo "  prev:         $PREV_OUTPUT"
    echo "═══════════════════════════════════════════"
    echo ""

    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "[dry-run] would call:"
        echo "  $WRAPPER cursor-agent -p \"...[PROMPT bytes ${#PROMPT_BODY}]...\""
        echo ""
        echo "----- PROMPT preview: first 48 lines -----"
        echo "$PROMPT_BODY" | head -n 48
        echo "----- ..."
    else
        "$WRAPPER" cursor-agent -p "$PROMPT_BODY"
    fi

    PREV_OUTPUT="$OUTPUT_PATH"
    export PREV_OUTPUT
}

# ---------- argparse ----------
COMMAND="${1:-}"
[[ -z "${COMMAND:-}" ]] && { usage; exit 2; }
shift || true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --execute)
            DRY_RUN=0
            shift
            ;;
        --topic)
            TOPIC_SLUG="$2"
            shift 2
            ;;
        --task)
            TASK="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            MODE="${MODE:+$MODE }${1}"
            shift
            ;;
    esac
done

TOKENS_AGG="$(echo "$MODE" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
export PREV_OUTPUT

if [[ "$COMMAND" == "list" ]]; then
    ensure_dirs
    echo "Stages: $STAGES_DIR"
    for f in "$STAGES_DIR"/*.md; do
        [[ -e "$f" ]] || continue
        stem=$(basename "$f" .md)
        sid=$(grep -m1 '^stage_id:' "$f" 2>/dev/null | cut -d: -f2- | sed -E 's/^[[:space:]]+//' | tr -d ' "\047' || echo "?")
        echo "  - $stem  stage_id=$sid"
    done
    exit 0
fi

if [[ -z "$TOKENS_AGG" ]]; then
    echo '[error] run STAGE | chain … 기본은 dry-run, 실제 실행은 --execute 필요' >&2
    usage
    exit 2
fi

ensure_dirs

if [[ "$COMMAND" == "run" ]]; then
    first="$(echo "$TOKENS_AGG" | awk '{print $1}')"
    [[ -z "$first" ]] && exit 2
    PREV_OUTPUT="${PREV_OUTPUT:-}"
    run_one_stage "$first"
    exit 0
fi

if [[ "$COMMAND" == "chain" ]]; then
    BATCH_NN_BASE="$(next_workspace_max_plus_one)"
    BATCH_STAGE_INDEX=0
    IFS=',' read -ra PARTS <<< "$TOKENS_AGG"
    for raw in "${PARTS[@]}"; do
        st="$(echo "$raw" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
        [[ -z "$st" ]] && continue
        run_one_stage "$st"
        BATCH_STAGE_INDEX=$((BATCH_STAGE_INDEX + 1))
    done
    exit 0
fi

echo "[error] 명령어: list | run | chain 만 지원합니다: $COMMAND" >&2
usage
exit 2
