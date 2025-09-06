"""Tests for openwebui state updates."""

from __future__ import annotations

import asyncio
from types import ModuleType, SimpleNamespace

import sys
import httpx

span_stub = SimpleNamespace(
    __enter__=lambda self: self,
    __exit__=lambda *a, **k: False,
    set_attribute=lambda *a, **k: None,
)
trace_stub = SimpleNamespace(start_as_current_span=lambda *a, **k: span_stub)
otel = ModuleType("opentelemetry")
otel.trace = SimpleNamespace(get_tracer=lambda *_a, **_k: trace_stub)
sys.modules.setdefault("opentelemetry", otel)
sys.modules.setdefault("opentelemetry.trace", otel.trace)
import tests.crown.server.test_server as srvtest
from fastapi import HTTPException

server = srvtest.server


def test_openwebui_chat_state_updates(monkeypatch):
    events: list[tuple[str, str]] = []
    bus = SimpleNamespace(publish_status=lambda c, s: events.append((c, s)))
    monkeypatch.setattr(server, "_LIFECYCLE_BUS", bus)

    called = {"log": False, "task": False}
    monkeypatch.setattr(
        server.corpus_memory_logging,
        "log_interaction",
        lambda *a, **k: called.__setitem__("log", True),
    )
    monkeypatch.setattr(
        server,
        "record_task_flow",
        lambda *a, **k: called.__setitem__("task", True),
    )

    async def run_request() -> int:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/openwebui-chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={"Authorization": "Bearer token"},
            )
        return resp.status_code

    status = asyncio.run(run_request())
    assert status == 200
    assert called["log"] and called["task"]
    assert events == [
        ("openwebui_session", "start"),
        ("openwebui_session", "end"),
    ]


def test_openwebui_chat_channel_state_updates(monkeypatch):
    events: list[tuple[str, str]] = []
    bus = SimpleNamespace(publish_status=lambda c, s: events.append((c, s)))
    monkeypatch.setattr(server, "_LIFECYCLE_BUS", bus)

    called = {"log": False, "task": False}
    monkeypatch.setattr(
        server.corpus_memory_logging,
        "log_interaction",
        lambda *a, **k: called.__setitem__("log", True),
    )
    monkeypatch.setattr(
        server,
        "record_task_flow",
        lambda *a, **k: called.__setitem__("task", True),
    )
    monkeypatch.setattr(
        server,
        "nazarick_chat",
        lambda ch, txt: {"text": "nazarick", "model": "stub"},
    )

    async def run_request() -> int:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/openwebui-chat",
                params={"channel": "nazarick"},
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={"Authorization": "Bearer token"},
            )
        return resp.status_code

    status = asyncio.run(run_request())
    assert status == 200
    assert called["log"] and called["task"]
    assert events == [
        ("openwebui_session", "start"),
        ("openwebui_session", "end"),
    ]


def test_openwebui_chat_invalid_channel_state_updates(monkeypatch):
    events: list[tuple[str, str]] = []
    bus = SimpleNamespace(publish_status=lambda c, s: events.append((c, s)))
    monkeypatch.setattr(server, "_LIFECYCLE_BUS", bus)

    called = {"log": False, "task": False}
    monkeypatch.setattr(
        server.corpus_memory_logging,
        "log_interaction",
        lambda *a, **k: called.__setitem__("log", True),
    )
    monkeypatch.setattr(
        server,
        "record_task_flow",
        lambda *a, **k: called.__setitem__("task", True),
    )

    def bad_channel(channel: str, text: str) -> dict[str, str]:
        raise HTTPException(status_code=404, detail="unknown channel")

    monkeypatch.setattr(server, "nazarick_chat", bad_channel)

    async def run_request() -> tuple[int, dict[str, object]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/openwebui-chat",
                params={"channel": "bad"},
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={"Authorization": "Bearer token"},
            )
        return resp.status_code, resp.json()

    status, data = asyncio.run(run_request())
    assert status == 404
    assert data["detail"] == "unknown channel"
    assert events == [
        ("openwebui_session", "start"),
        ("openwebui_session", "end"),
    ]
    assert not called["log"] and not called["task"]
