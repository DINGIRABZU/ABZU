from __future__ import annotations

import importlib.util
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def test_external_connector_uses_http_when_mcp_active(monkeypatch):
    called: dict[str, bool] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # type: ignore[override]
            called["hit"] = True
            self.send_response(200)
            self.end_headers()
            # consume request body
            _ = self.rfile.read(int(self.headers.get("Content-Length", "0")))

        def log_message(self, *_: object) -> None:  # pragma: no cover - quiet
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    monkeypatch.setenv("PRIMORDIALS_API_URL", url)
    monkeypatch.setenv("ABZU_USE_MCP", "1")

    # Import connector after environment is configured so it picks up the URL.
    spec = importlib.util.spec_from_file_location(
        "primordials_api",
        Path(__file__).resolve().parents[2] / "connectors" / "primordials_api.py",
    )
    primordials_api = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(primordials_api)

    try:
        assert primordials_api.send_metrics({"foo": "bar"})
        assert called.get("hit")
    finally:
        server.shutdown()
