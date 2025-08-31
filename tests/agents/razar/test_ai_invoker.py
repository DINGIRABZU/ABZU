from __future__ import annotations

__version__ = "0.2.2"

import json
from types import SimpleNamespace
from pathlib import Path

import agents.razar.ai_invoker as ai_invoker


def test_handover_returns_suggestion_and_logs(monkeypatch, tmp_path: Path) -> None:
    def fake_loader(name: str, url: str, patch_context=None):
        assert name == "test"
        assert url == "http://example.com/agent.py"
        assert patch_context == {"failure": "ctx", "auth_token": "TOKEN"}
        return SimpleNamespace(__name__=name), {"config": True}, {"patch": "data"}

    monkeypatch.setattr(ai_invoker.remote_loader, "load_remote_agent", fake_loader)
    inv_log = tmp_path / "invocations.json"
    patch_log = tmp_path / "patches.json"
    monkeypatch.setattr(ai_invoker, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", patch_log)

    config = {
        "active": "test",
        "agents": [
            {
                "name": "test",
                "endpoint": "http://example.com/agent.py",
                "auth": {"token": "TOKEN"},
            }
        ],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    suggestion = ai_invoker.handover(
        config_path=config_path, context={"failure": "ctx"}
    )
    assert suggestion == {"patch": "data"}

    inv_records = json.loads(inv_log.read_text(encoding="utf-8"))
    assert inv_records[0]["event"] == "invocation"
    assert inv_records[0]["name"] == "test"
    assert inv_records[0]["endpoint"] == "http://example.com/agent.py"
    assert inv_records[0]["context"] == {"failure": "ctx"}

    patch_records = json.loads(patch_log.read_text(encoding="utf-8"))
    assert patch_records[0]["event"] == "suggestion"
    assert patch_records[0]["name"] == "test"
    assert patch_records[0]["config"] == {"config": True}
    assert patch_records[0]["suggestion"] == {"patch": "data"}


def test_handover_returns_confirmation(monkeypatch, tmp_path: Path) -> None:
    def fake_loader(name: str, url: str, patch_context=None):
        assert patch_context is None
        return SimpleNamespace(__name__=name), {}, None

    monkeypatch.setattr(ai_invoker.remote_loader, "load_remote_agent", fake_loader)
    inv_log = tmp_path / "invocations.json"
    patch_log = tmp_path / "patches.json"
    monkeypatch.setattr(ai_invoker, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", patch_log)

    config = {
        "agents": [{"name": "alpha", "endpoint": "http://example.com/a.py"}],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = ai_invoker.handover(config_path=config_path)
    assert result == {"handover": True}

    inv_records = json.loads(inv_log.read_text(encoding="utf-8"))
    assert inv_records[0]["event"] == "invocation"
    assert inv_records[0]["name"] == "alpha"
    assert inv_records[0]["endpoint"] == "http://example.com/a.py"

    patch_records = json.loads(patch_log.read_text(encoding="utf-8"))
    assert patch_records[0]["event"] == "no_suggestion"
    assert patch_records[0]["name"] == "alpha"
    assert "suggestion" not in patch_records[0]
