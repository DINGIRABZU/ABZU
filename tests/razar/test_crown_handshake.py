"""Integration coverage for the Crown handshake transcript."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any, Dict

from tests.conftest import allow_test

allow_test(__file__)

import pytest

from razar.crown_handshake import CrownHandshake
from tests.razar.conftest import (
    EXPECTED_IDENTITY_MODIFIED,
    EXPECTED_IDENTITY_SHA256,
)


class _StubWebSocket:
    """Context manager that mimics a websocket connection."""

    def __init__(self, reply: Dict[str, Any]) -> None:
        self._reply = reply
        self.sent_payload: dict[str, Any] | None = None

    async def __aenter__(self) -> "_StubWebSocket":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def send(self, payload: str) -> None:
        self.sent_payload = json.loads(payload)

    async def recv(self) -> str:
        return json.dumps(self._reply)


@pytest.mark.usefixtures("identity_summary_file")
def test_transcript_includes_fingerprint_and_capabilities(
    monkeypatch,
    tmp_path,
    identity_fingerprint,
):
    """Verify the transcript contains the identity fingerprint and capabilities."""

    mission_brief = {
        "priority_map": {"core": 1},
        "current_status": {"core": "green"},
        "open_issues": [],
    }
    mission_path = tmp_path / "mission.json"
    mission_path.write_text(json.dumps(mission_brief))

    transcript_path = tmp_path / "dialogue.json"

    reply_body = {
        "ack": "CROWN-ACK",
        "capabilities": ["triage", "diagnostics"],
        "downtime": {},
    }
    connection = _StubWebSocket(reply_body)

    def _fake_connect(url: str) -> _StubWebSocket:
        assert url == "ws://unit-test"
        return connection

    monkeypatch.setenv("CROWN_IDENTITY_FINGERPRINT", json.dumps(identity_fingerprint))
    monkeypatch.setattr(
        "razar.crown_handshake.websockets",
        SimpleNamespace(connect=_fake_connect),
    )

    handshake = CrownHandshake("ws://unit-test", transcript_path)
    response = asyncio.run(handshake.perform(str(mission_path)))

    assert response.capabilities == ["triage", "diagnostics"]
    assert response.identity_fingerprint == identity_fingerprint
    assert response.identity_fingerprint["sha256"] == EXPECTED_IDENTITY_SHA256
    assert response.identity_fingerprint["modified"] == EXPECTED_IDENTITY_MODIFIED

    assert connection.sent_payload == mission_brief

    transcript = json.loads(transcript_path.read_text())
    assert transcript[-1]["message"]["identity_fingerprint"] == identity_fingerprint
    assert transcript[-1]["message"]["capabilities"] == ["triage", "diagnostics"]
