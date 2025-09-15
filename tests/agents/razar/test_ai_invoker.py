"""Tests for ai invoker."""

from __future__ import annotations

__version__ = "0.2.3"

import json
from types import SimpleNamespace
from pathlib import Path
from typing import Any

import pytest

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


def test_handover_applies_code_repair(monkeypatch, tmp_path: Path) -> None:
    module_file = tmp_path / "mod.py"
    test_file = tmp_path / "test_mod.py"
    suggestion = {
        "module": str(module_file),
        "tests": [str(test_file)],
        "error": "boom",
    }

    def fake_loader(name: str, url: str, patch_context=None):
        return SimpleNamespace(__name__=name), {}, suggestion

    called: dict[str, Any] = {}

    def fake_repair(module_path: Path, tests, error, *, models=None):
        called["module"] = module_path
        called["tests"] = list(tests)
        called["error"] = error
        return True

    monkeypatch.setattr(ai_invoker.remote_loader, "load_remote_agent", fake_loader)
    monkeypatch.setattr(ai_invoker.code_repair, "repair_module", fake_repair)

    inv_log = tmp_path / "inv.json"
    patch_log = tmp_path / "patch.json"
    monkeypatch.setattr(ai_invoker, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", patch_log)

    config = {"agents": [{"name": "beta", "endpoint": "http://agent"}]}
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")

    result = ai_invoker.handover(config_path=cfg)
    assert result == suggestion
    assert called["module"] == module_file
    assert called["tests"] == [test_file]
    assert called["error"] == "boom"

    log = json.loads(patch_log.read_text(encoding="utf-8"))
    assert log[0]["applied"] is True


def test_handover_uses_kimi2_adapter(monkeypatch, tmp_path: Path) -> None:
    module_file = tmp_path / "module.py"
    test_file = tmp_path / "test_module.py"
    suggestion = {
        "module": str(module_file),
        "tests": [str(test_file)],
        "error": "boom",
    }

    called: dict[str, Any] = {}

    class DummyResponse:
        status_code = 200
        text = json.dumps(suggestion)

        def raise_for_status(self) -> None:
            return None

        def json(self) -> Any:
            return suggestion

    def fake_post(url: str, *, json=None, headers=None, timeout=None):
        called["url"] = url
        called["json"] = json
        called["headers"] = headers
        called["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(ai_invoker.requests, "post", fake_post)
    monkeypatch.setattr(
        ai_invoker.remote_loader,
        "load_remote_agent",
        lambda *args, **kwargs: pytest.fail("remote_loader should not be used"),
    )

    def fake_repair(module_path, tests, error):
        return True

    monkeypatch.setattr(ai_invoker.code_repair, "repair_module", fake_repair)

    inv_log = tmp_path / "invocations.json"
    patch_log = tmp_path / "patches.json"
    monkeypatch.setattr(ai_invoker, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", patch_log)

    config = {
        "active": "kimi2",
        "agents": [
            {
                "name": "kimi2",
                "endpoint": "http://kimi.local/patch",
                "auth": {"token": "TOKEN"},
            }
        ],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = ai_invoker.handover(config_path=config_path, context={"component": "demo"})
    assert result == suggestion

    assert called["url"] == "http://kimi.local/patch"
    assert called["json"]["component"] == "demo"
    assert called["json"]["auth_token"] == "TOKEN"
    assert called["headers"]["Authorization"] == "Bearer TOKEN"
    assert called["headers"]["X-API-Key"] == "TOKEN"
    assert called["timeout"] == 60.0

    log = json.loads(patch_log.read_text(encoding="utf-8"))
    assert log[0]["config"]["service"] == "kimi2"
