from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from communication import command_dispatch


def test_dispatch_and_verify(tmp_path, monkeypatch):
    module = importlib.reload(command_dispatch)

    calls: list[str] = []

    def handler(cmd: str) -> None:
        calls.append(cmd)

    module.register_agent("alpha", handler)
    monkeypatch.setattr(module, "STORAGE_DIR", Path(tmp_path))

    client = TestClient(module.app)

    # Non-critical channel should not mirror events
    resp = client.post(
        "/dispatch",
        json={
            "operator": "op",
            "agent": "alpha",
            "channel": "general",
            "command": "ping",
        },
    )
    assert resp.status_code == 200
    assert calls == ["ping"]
    assert not list(Path(tmp_path).rglob("*.json"))

    critical = next(iter(module.CRITICAL_CHANNELS))
    resp = client.post(
        "/dispatch",
        json={
            "operator": "op",
            "agent": "alpha",
            "channel": critical,
            "command": "pong",
        },
    )
    assert resp.status_code == 200
    event_id = resp.json()["event_id"]
    mirrored = Path(tmp_path) / critical / f"{event_id}.json"
    assert mirrored.exists()
    assert mirrored.stat().st_mode & 0o222 == 0  # read-only

    verify = client.get(f"/verify/{event_id}")
    assert verify.status_code == 200
    assert verify.json()["command"] == "pong"
