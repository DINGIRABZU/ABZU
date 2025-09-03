"""Tests for launch_servants.sh behavior."""

import os
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import urllib.request

import yaml


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - required method name
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:  # pragma: no cover - unused path
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # pragma: no cover - silence server
        return


def _start_health_server(port: int) -> HTTPServer:
    server = HTTPServer(("127.0.0.1", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_launch_servants_creates_endpoints_and_checks_health(tmp_path):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = _start_health_server(port)

    root = Path(__file__).resolve().parents[3]
    secrets = root / "secrets.env"
    secrets.write_text(
        f'SERVANT_MODELS="foo=http://127.0.0.1:{port}"\n', encoding="utf-8"
    )

    config = {"components": [{"name": "stub", "priority": 1, "command": "echo stub"}]}
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(yaml.safe_dump(config), encoding="utf-8")

    endpoints = tmp_path / "endpoints.txt"
    env = os.environ | {
        "RAZAR_CONFIG": str(cfg),
        "SERVANT_ENDPOINTS_FILE": str(endpoints),
        "SERVANT_TIMEOUT": "5",
    }

    subprocess.run(
        ["bash", str(root / "launch_servants.sh")], check=True, cwd=root, env=env
    )

    # Ensure the endpoints file was written with the expected URL
    assert (
        endpoints.read_text(encoding="utf-8").strip() == f"foo=http://127.0.0.1:{port}"
    )

    # Health endpoint should respond successfully
    resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5)
    assert resp.status == 200
    resp.close()

    server.shutdown()
    secrets.unlink()
