"""Tests for MCP usage in bot connectors."""

from __future__ import annotations

from types import SimpleNamespace
import importlib
import sys
import types

# Stub connector dependencies to avoid heavy imports
bus_mod = types.ModuleType("connectors.signal_bus")
bus_mod.publish = lambda *a, **k: None
bus_mod.subscribe = lambda *a, **k: None
fmt_mod = types.ModuleType("connectors.message_formatter")
fmt_mod.format_message = lambda chakra, text: text
base_mod = types.ModuleType("connectors.base")
base_mod.ConnectorHeartbeat = object
sys.modules["connectors"] = types.ModuleType("connectors")
sys.modules["connectors.signal_bus"] = bus_mod
sys.modules["connectors.message_formatter"] = fmt_mod
sys.modules["connectors.base"] = base_mod

bot_discord = importlib.import_module("tools.bot_discord")
bot_telegram = importlib.import_module("tools.bot_telegram")


def _fake_post(url, json, timeout):
    """Capture POST calls for inspection."""
    _fake_post.last = SimpleNamespace(url=url, json=json)

    class Resp:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, str]:
            return {"result": "ok"}

    return Resp()


def test_discord_send_glm_command_mcp(monkeypatch):
    monkeypatch.setattr(bot_discord, "_USE_MCP", True)
    monkeypatch.setattr(bot_discord, "_MCP_URL", "http://mcp")
    monkeypatch.setattr(bot_discord, "requests", SimpleNamespace(post=_fake_post))
    out = bot_discord.send_glm_command("hi")
    assert out == "ok"
    assert _fake_post.last.url == "http://mcp/model/invoke"
    assert _fake_post.last.json == {"model": "glm", "text": "hi"}


def test_telegram_send_glm_command_mcp(monkeypatch):
    monkeypatch.setattr(bot_telegram, "_USE_MCP", True)
    monkeypatch.setattr(bot_telegram, "_MCP_URL", "http://mcp")
    monkeypatch.setattr(bot_telegram, "requests", SimpleNamespace(post=_fake_post))
    out = bot_telegram.send_glm_command("hi")
    assert out == "ok"
    assert _fake_post.last.url == "http://mcp/model/invoke"
    assert _fake_post.last.json == {"model": "glm", "text": "hi"}
