from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path

import agents.razar.ai_invoker as ai_invoker


def test_handover_returns_suggestion_and_logs(monkeypatch, tmp_path: Path) -> None:
    def fake_loader(name: str, url: str, patch_context=None):
        assert name == "test"
        assert url == "http://example.com/agent.py"
        assert patch_context == "ctx"
        return SimpleNamespace(__name__=name), {"config": True}, {"patch": "data"}

    monkeypatch.setattr(ai_invoker.remote_loader, "load_remote_agent", fake_loader)
    log_path = tmp_path / "invocations.json"
    monkeypatch.setattr(ai_invoker, "LOG_PATH", log_path)

    config = {
        "active": "test",
        "agents": [{"name": "test", "url": "http://example.com/agent.py"}],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    suggestion = ai_invoker.handover(config_path=config_path, patch_context="ctx")
    assert suggestion == {"patch": "data"}

    records = json.loads(log_path.read_text(encoding="utf-8"))
    assert records[0]["name"] == "test"
    assert records[0]["config"] == {"config": True}
    assert records[0]["suggestion"] == {"patch": "data"}


def test_handover_returns_confirmation(monkeypatch, tmp_path: Path) -> None:
    def fake_loader(name: str, url: str, patch_context=None):
        return SimpleNamespace(__name__=name), {}, None

    monkeypatch.setattr(ai_invoker.remote_loader, "load_remote_agent", fake_loader)
    log_path = tmp_path / "invocations.json"
    monkeypatch.setattr(ai_invoker, "LOG_PATH", log_path)

    config = {
        "agents": [{"name": "alpha", "url": "http://example.com/a.py"}],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = ai_invoker.handover(config_path=config_path)
    assert result == {"handover": True}

    records = json.loads(log_path.read_text(encoding="utf-8"))
    assert records[0]["name"] == "alpha"
    assert "suggestion" not in records[0]
