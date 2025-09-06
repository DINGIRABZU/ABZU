from __future__ import annotations

import asyncio
import tests.crown.server.test_server as base
import httpx
import pytest

server = base.server
settings = base.settings


def _auth_headers() -> dict[str, str]:
    async def _login() -> str:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/token", data={"username": "user", "password": "pass"}
            )
        return resp.json()["access_token"]

    token = asyncio.run(_login())
    return {"Authorization": f"Bearer {token}"}


def test_openwebui_defaults_to_crown(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, str] = {}

    def fake_crown(msg: str, _glm) -> dict[str, str]:
        called["msg"] = msg
        return {"text": "crown", "model": "stub"}

    def fail(*_a, **_k):  # pragma: no cover - should not route
        raise AssertionError("nazarick called")

    monkeypatch.setattr(server, "crown_prompt_orchestrator", fake_crown)
    monkeypatch.setattr(server, "nazarick_chat", fail)

    async def run() -> tuple[int, dict[str, object]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/openwebui-chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers=_auth_headers(),
            )
        return resp.status_code, resp.json()

    status, data = asyncio.run(run())
    assert status == 200
    assert called["msg"] == "hi"
    assert data["choices"][0]["message"]["content"] == "crown"


def test_openwebui_routes_to_nazarick(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, str] = {}

    def fake_nazarick(channel: str, text: str) -> dict[str, str]:
        called["channel"] = channel
        called["text"] = text
        return {"text": "nazarick", "model": "stub"}

    def fail(*_a, **_k):  # pragma: no cover - should not route
        raise AssertionError("crown called")

    monkeypatch.setattr(server, "nazarick_chat", fake_nazarick)
    monkeypatch.setattr(server, "crown_prompt_orchestrator", fail)

    async def run() -> tuple[int, dict[str, object]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/openwebui-chat",
                params={"channel": "#signal-hall"},
                json={"messages": [{"role": "user", "content": "hello"}]},
                headers=_auth_headers(),
            )
        return resp.status_code, resp.json()

    status, data = asyncio.run(run())
    assert status == 200
    assert called["channel"] == "#signal-hall"
    assert called["text"] == "hello"
    assert data["choices"][0]["message"]["content"] == "nazarick"
