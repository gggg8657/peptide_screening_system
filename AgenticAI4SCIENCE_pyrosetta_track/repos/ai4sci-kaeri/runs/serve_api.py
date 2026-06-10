#!/usr/bin/env python3
"""
Pipeline Status API Server
============================
프론트엔드 대시보드에 파이프라인 상태를 제공하는 CORS-enabled HTTP 서버.

Usage:
    python runs/serve_api.py          # http://localhost:8787
    python runs/serve_api.py 9090     # http://localhost:9090

프론트엔드에서 http://localhost:8787/api/status 로 폴링합니다.
"""

from __future__ import annotations

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = ROOT / "runs" / "live_demo" / "pipeline_status.json"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787


class CORSHandler(BaseHTTPRequestHandler):
    """CORS-enabled JSON API handler."""

    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in ("/api/status", "/api/status/"):
            self._serve_status()
        elif self.path == "/health":
            self._serve_health()
        else:
            self.send_error(404, "Not Found. Use /api/status or /health")

    def _serve_status(self) -> None:
        if not STATUS_FILE.exists():
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "run_id": "",
                "steps": [],
                "agents": [],
                "candidates": [],
                "qc_gates": [],
                "convergence": [],
                "live_apis": {"esmfold": "pending", "molmim": "pending"},
                "completed": False,
                "message": "Pipeline not started. Run: python runs/run_live_demo.py",
            }).encode())
            return

        data = STATUS_FILE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def _serve_health(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "status_file": str(STATUS_FILE),
            "file_exists": STATUS_FILE.exists(),
        }).encode())

    def log_message(self, format: str, *args) -> None:
        # Compact logging
        if args and "/api/status" in str(args[0]):
            return  # Suppress frequent poll logs
        super().log_message(format, *args)


def main() -> None:
    server = HTTPServer(("0.0.0.0", PORT), CORSHandler)
    print(f"🔬 Pipeline Status API Server")
    print(f"   URL:    http://localhost:{PORT}/api/status")
    print(f"   Health: http://localhost:{PORT}/health")
    print(f"   File:   {STATUS_FILE}")
    print(f"   Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
