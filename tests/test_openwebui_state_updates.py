from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import tests.test_server as srvtest

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
