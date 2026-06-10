#!/usr/bin/env bash
# Compile .mermaid / .mmd files to SVG (and optionally PNG) using @mermaid-js/mermaid-cli.
# Requires: Node.js, npx
# Usage: ./scripts/compile_mermaid.sh [input.mermaid] [output_dir]
#  Default: input = pipeline_orchestration.mermaid, output_dir = docs

set -e
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="${1:-$REPO/pipeline_orchestration.mermaid}"
OUT_DIR="${2:-$REPO/docs}"
mkdir -p "$OUT_DIR"
BASE="$(basename "$INPUT" .mermaid)"
BASE="${BASE%.mmd}"
OUT_SVG="$OUT_DIR/${BASE}.svg"

echo "Compiling: $INPUT -> $OUT_SVG"
npx -y @mermaid-js/mermaid-cli@latest -i "$INPUT" -o "$OUT_SVG"
echo "Done: $OUT_SVG"
