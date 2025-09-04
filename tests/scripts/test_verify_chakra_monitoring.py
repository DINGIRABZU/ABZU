from __future__ import annotations
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from scripts.verify_chakra_monitoring import verify_chakra_monitoring


class _MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # pragma: no cover - simple server
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"test_metric 1\n")

    def log_message(self, format: str, *args: object) -> None:  # pragma: no cover
        return


def _serve(port: int) -> HTTPServer:
    server = HTTPServer(("localhost", port), _MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


@pytest.fixture
def exporters(monkeypatch: pytest.MonkeyPatch) -> None:
    servers: list[HTTPServer] = []
    urls: list[str] = []
    for _ in range(3):
        sock = socket.socket()
        sock.bind(("localhost", 0))
        port = sock.getsockname()[1]
        sock.close()
        servers.append(_serve(port))
        urls.append(f"http://localhost:{port}/metrics")
    monkeypatch.setenv("CHAKRA_EXPORTERS", ",".join(urls))
    yield
    for server in servers:
        server.shutdown()


def test_verify_chakra_monitoring(exporters: None) -> None:
    assert verify_chakra_monitoring() == 0
