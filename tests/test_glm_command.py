"""Ensure the GLM command endpoint enforces auth and filters commands."""

from __future__ import annotations

import asyncio
import importlib

import httpx

from crown_config import settings

settings.glm_command_token = "token"
server = importlib.reload(importlib.import_module("server"))


async def _post(command: str, headers: dict[str, str] | None = None):
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.post(
            "/glm-command", json={"command": command}, headers=headers or {}
        )


def test_authorized_command(monkeypatch):
    monkeypatch.setattr(server, "send_command", lambda c: f"ran {c}")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda t, m: None)
    resp = asyncio.run(_post("ls", {"Authorization": "token"}))
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "result": "ran ls"}


def test_missing_token(monkeypatch):
    monkeypatch.setattr(server, "send_command", lambda c: "out")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda t, m: None)
    resp = asyncio.run(_post("ls"))
    assert resp.status_code == 401


def test_disallowed_command(monkeypatch):
    monkeypatch.setattr(server, "send_command", lambda c: "out")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda t, m: None)
    resp = asyncio.run(_post("echo hi", {"Authorization": "token"}))
    assert resp.status_code == 400
