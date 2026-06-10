#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

if [[ $# -ge 1 ]]; then
  PORT="$1"
else
  PORT=$(python3 - <<'PY'
import socket
for port in range(8765, 8781):
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            continue
        print(port)
        break
PY
)
fi

if [[ -z "${PORT}" ]]; then
  echo "No free port found in 8765-8780" >&2
  exit 1
fi

echo "Starting benchmark UI on http://127.0.0.1:${PORT}"
exec python3 llm_benchmark/ui/server.py --host 127.0.0.1 --port "${PORT}"
