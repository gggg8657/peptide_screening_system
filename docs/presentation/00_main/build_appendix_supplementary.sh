#!/usr/bin/env bash
# 통합 부록·Selectivity 보충: Markdown → HTML(pandoc) → PDF(Chrome headless)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

CSS="_md_doc_style.css"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
if [[ ! -x "$CHROME" ]]; then
  CHROME="/Applications/Chromium.app/Contents/MacOS/Chromium"
fi
if [[ ! -x "$CHROME" ]]; then
  echo "Chrome/Chromium 실행 파일을 찾을 수 없습니다. CHROME 환경변수로 경로를 지정하세요." >&2
  exit 1
fi

build_one() {
  local md="$1" title="$2"
  local base="${md%.md}"
  pandoc "$md" -s --toc --metadata "title=$title" --css="$CSS" -o "${base}.html"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$DIR/${base}.pdf" \
    "file://$DIR/${base}.html"
  echo "OK ${base}.html ${base}.pdf"
}

build_one "05_unified_appendix.md" "통합 부록 — SSTR2 방사성의약품 AI Co-Scientist"
build_one "06_selectivity_supplementary.md" "Selectivity 보충 — Off-target 분석"
