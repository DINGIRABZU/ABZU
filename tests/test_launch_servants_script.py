from __future__ import annotations

import os
import shutil
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SKIP = shutil.which("bash") is None or not os.access(
    ROOT / "launch_servants.sh", os.X_OK
)
pytestmark = pytest.mark.skipif(
    SKIP, reason="requires bash and executable launch_servants.sh"
)


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # pragma: no cover - called in separate thread
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_launch_servants_records_reachable(tmp_path):
    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    endpoints = tmp_path / "endpoints.txt"
    secret = ROOT / "secrets.env"
    backup = secret.with_suffix(".bak")
    secret.rename(backup)
    try:
        secret.write_text(f"SERVANT_MODELS=test=http://127.0.0.1:{port}\n")
        env = os.environ.copy()
        env.update(
            {
                "SERVANT_ENDPOINTS_FILE": str(endpoints),
                "SERVANT_TIMEOUT": "5",
            }
        )
        result = subprocess.run(
            ["bash", str(ROOT / "launch_servants.sh")],
            env=env,
        )
    finally:
        secret.unlink(missing_ok=True)
        backup.rename(secret)
        server.shutdown()
        thread.join()

    assert result.returncode == 0
    assert endpoints.read_text().strip() == f"test=http://127.0.0.1:{port}"


def test_launch_servants_fails_when_unreachable(tmp_path):
    port = _free_port()
    endpoints = tmp_path / "endpoints.txt"
    secret = ROOT / "secrets.env"
    backup = secret.with_suffix(".bak")
    secret.rename(backup)
    try:
        secret.write_text(f"SERVANT_MODELS=test=http://127.0.0.1:{port}\n")
        env = os.environ.copy()
        env.update(
            {
                "SERVANT_ENDPOINTS_FILE": str(endpoints),
                "SERVANT_TIMEOUT": "1",
            }
        )
        result = subprocess.run(
            ["bash", str(ROOT / "launch_servants.sh")],
            env=env,
        )
    finally:
        secret.unlink(missing_ok=True)
        backup.rename(secret)

    assert result.returncode != 0
