import builtins
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from neoabzu_kimicho import init_kimicho
from neoabzu_razar import route


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # pragma: no cover - simple test server
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"text":"pong"}')

    def log_message(self, format, *args):  # pragma: no cover - suppress
        pass


def test_route_falls_back_to_kimicho_when_crown_unavailable():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        url = f"http://{server.server_address[0]}:{server.server_address[1]}"
        init_kimicho(url)
        orig_import = builtins.__import__

        def _fail_import(name, *args, **kwargs):
            if name == "neoabzu_crown":
                raise ImportError("mock crown down")
            return orig_import(name, *args, **kwargs)

        builtins.__import__ = _fail_import
        try:
            res = route("ping", "joy")
        finally:
            builtins.__import__ = orig_import
        assert res["text"] == "pong"
    finally:
        server.shutdown()
        thread.join()
