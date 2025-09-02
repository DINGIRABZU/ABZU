"""Tests for remote loader."""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import importlib.util

repo_root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "remote_loader", repo_root / "agents" / "razar" / "remote_loader.py"
)
remote_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote_loader)


def _start_server(directory: Path) -> tuple[ThreadingHTTPServer, threading.Thread]:
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    return httpd, thread


def test_patch_on_failure(tmp_path: Path) -> None:
    module_path = repo_root / "temp_remote_module.py"
    module_path.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")

    test_file = tmp_path / "test_temp_remote_module.py"
    test_file.write_text(
        "from temp_remote_module import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    agent_code = (
        "def configure():\n    return {'name': 'patcher'}\n\n"
        'def patch(context=None):\n    return "def add(a, b):\\n    return a + b\\n"\n'
    )
    (agent_dir / "remote_agent.py").write_text(agent_code, encoding="utf-8")

    httpd, thread = _start_server(agent_dir)
    url = f"http://localhost:{httpd.server_port}/remote_agent.py"
    try:
        success = remote_loader.patch_on_test_failure(
            "remote_agent", url, module_path, [test_file]
        )
        assert success
        assert "return a + b" in module_path.read_text(encoding="utf-8")
    finally:
        httpd.shutdown()
        thread.join()
        module_path.unlink(missing_ok=True)
