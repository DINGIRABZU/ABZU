"""Tests for crown handshake."""

import asyncio
import json
import types
from pathlib import Path

import pytest

from razar import crown_handshake as ch

__version__ = "0.1.0"


@pytest.fixture
def mock_ws(monkeypatch):
    """Mock websockets connect for handshake."""

    class DummyWS:
        async def send(self, data):  # pragma: no cover - trivial
            self.sent = data

        async def recv(self):
            return json.dumps(
                {
                    "ack": "ok",
                    "capabilities": ["GLM4V"],
                    "downtime": {"alpha": {"patch": 1}},
                }
            )

    class DummyCM:
        async def __aenter__(self):
            return DummyWS()

        async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - trivial
            return False

    monkeypatch.setattr(
        ch,
        "websockets",
        types.SimpleNamespace(connect=lambda url: DummyCM()),
    )


def test_handshake_records_and_recovers(tmp_path: Path, mock_ws, monkeypatch) -> None:
    transcript = tmp_path / "dialogues.json"

    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        ch.recovery_manager, "request_shutdown", lambda c: calls.append(("down", c))
    )
    monkeypatch.setattr(
        ch.recovery_manager, "apply_patch", lambda c, p: calls.append(("patch", c, p))
    )
    monkeypatch.setattr(
        ch.recovery_manager, "resume", lambda c: calls.append(("up", c))
    )

    brief = tmp_path / "brief.json"
    brief.write_text(
        json.dumps({"priority_map": {"a": 0}, "current_status": {}, "open_issues": []})
    )

    handshake = ch.CrownHandshake("ws://dummy", transcript)
    resp = asyncio.run(handshake.perform(str(brief)))

    assert resp.capabilities == ["GLM4V"]
    assert calls == [
        ("down", "alpha"),
        ("patch", "alpha", {"patch": 1}),
        ("up", "alpha"),
    ]
    log = json.loads(transcript.read_text())
    assert [entry["role"] for entry in log] == ["razar", "crown"]
