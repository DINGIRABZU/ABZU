import sys
from types import ModuleType
from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import INANNA_AI.glm_integration as gi


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def json(self):
        return {"text": self.text}

    def raise_for_status(self):
        return None


def test_send_command(monkeypatch):
    calls = {}
    dummy = ModuleType("requests")

    def post(url, json=None, timeout=10, headers=None):
        calls["url"] = url
        calls["payload"] = json
        calls["headers"] = headers
        return DummyResponse("pong")

    dummy.post = post
    dummy.RequestException = Exception
    monkeypatch.setattr(gi, "requests", dummy)

    monkeypatch.setenv("GLM_SHELL_URL", "http://shell")
    monkeypatch.setenv("GLM_SHELL_KEY", "secret")

    sys.modules.pop("glm_shell", None)
    glm_shell = importlib.import_module("glm_shell")

    out = glm_shell.send_command("ls -la")
    assert out == "pong"
    assert calls["url"] == "http://shell"
    assert calls["payload"] == {"prompt": "[shell]ls -la", "temperature": 0.8}
    assert calls["headers"] == {"Authorization": "Bearer secret"}
