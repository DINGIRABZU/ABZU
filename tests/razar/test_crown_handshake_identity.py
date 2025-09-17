"""Regression coverage for propagating the identity fingerprint."""

from __future__ import annotations

import json
import asyncio
from types import SimpleNamespace
from typing import Any, Dict

from tests.conftest import allow_test

allow_test(__file__)

from razar.crown_handshake import CrownHandshake


class _StubConnection:
    """Minimal async context manager that mimics a websocket connection."""

    def __init__(self, reply: Dict[str, Any]) -> None:
        self._reply = reply
        self.sent_payload: str | None = None

    async def __aenter__(self) -> "_StubConnection":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def send(self, payload: str) -> None:
        self.sent_payload = payload

    async def recv(self) -> str:
        return json.dumps(self._reply)


def test_identity_fingerprint_written_to_transcript(monkeypatch, tmp_path):
    """Ensure the handshake persists the fingerprint in logs and responses."""

    mission_brief = {
        "priority_map": {"fusion": 1},
        "current_status": {"fusion": "green"},
        "open_issues": [],
    }
    mission_path = tmp_path / "brief.json"
    mission_path.write_text(json.dumps(mission_brief))

    transcript_path = tmp_path / "transcript.json"

    fingerprint_payload = {
        "sha256": "abc123",
        "modified": "2024-01-01T00:00:00+00:00",
    }
    monkeypatch.setenv("CROWN_IDENTITY_FINGERPRINT", json.dumps(fingerprint_payload))

    reply_body = {"ack": "CROWN-ACK", "capabilities": ["stasis"], "downtime": {}}
    connection = _StubConnection(reply_body)

    def _fake_connect(url: str) -> _StubConnection:
        assert url == "ws://example.com/crown"
        return connection

    monkeypatch.setattr(
        "razar.crown_handshake.websockets",
        SimpleNamespace(connect=_fake_connect),
    )

    handshake = CrownHandshake("ws://example.com/crown", transcript_path)
    response = asyncio.run(handshake.perform(str(mission_path)))

    assert response.identity_fingerprint == fingerprint_payload

    transcript = json.loads(transcript_path.read_text())
    assert transcript[-1]["message"]["identity_fingerprint"] == fingerprint_payload
