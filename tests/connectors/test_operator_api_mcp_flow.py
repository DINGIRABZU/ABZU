import importlib
import time
from typing import Any, Mapping

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import allow_test

allow_test(__file__)


class DummyAdapter:
    instances: list["DummyAdapter"] = []

    def __init__(self, *_: Any, **__: Any) -> None:
        self.handshake_calls = 0
        self.heartbeat_payloads: list[tuple[Mapping[str, Any], Any]] = []
        self.started = False
        self.stopped = False
        self._interval = 0.01
        DummyAdapter.instances.append(self)

    async def ensure_handshake(self) -> Mapping[str, Any]:
        self.handshake_calls += 1
        return {
            "session": {
                "id": f"session-{self.handshake_calls}",
                "credential_expiry": "2025-01-01T00:00:00Z",
            }
        }

    async def emit_stage_b_heartbeat(
        self, payload: Mapping[str, Any], *, credential_expiry: Any = None
    ) -> Mapping[str, Any]:
        self.heartbeat_payloads.append((payload, credential_expiry))
        return dict(payload)

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_operator_api_handshake_and_heartbeat(monkeypatch):
    monkeypatch.setenv("ABZU_USE_MCP", "1")
    import operator_api

    importlib.reload(operator_api)

    DummyAdapter.instances.clear()
    monkeypatch.setattr(operator_api, "OperatorMCPAdapter", DummyAdapter)

    rotations: list[str] = []

    def fake_record(connector_id: str, **_: Any) -> dict[str, Any]:
        rotations.append(connector_id)
        return {"connector_id": connector_id}

    async def fake_broadcast(_: Mapping[str, Any]) -> None:
        return None

    monkeypatch.setattr(operator_api, "record_rotation_drill", fake_record)
    monkeypatch.setattr(operator_api, "broadcast_event", fake_broadcast)
    monkeypatch.setattr(
        operator_api._dispatcher,
        "dispatch",
        lambda *args, **kwargs: {"dispatched": True},
    )

    app = FastAPI()
    app.include_router(operator_api.router)

    with TestClient(app) as client:
        # Allow startup tasks and heartbeats to run
        time.sleep(0.05)
        assert DummyAdapter.instances, "MCP adapter was not instantiated"
        adapter = DummyAdapter.instances[0]
        assert adapter.handshake_calls >= 1
        assert adapter.started is True
        assert rotations.count("operator_api") == 1
        assert rotations.count("operator_upload") == 1
        assert adapter.heartbeat_payloads, "heartbeat loop did not execute"

        # Force a new handshake before serving a command request
        operator_api._MCP_SESSION = None
        response = client.post(
            "/operator/command",
            json={"operator": "overlord", "agent": "victim", "command": "noop"},
        )
        assert response.status_code == 200
        assert adapter.handshake_calls >= 2

    # Shutdown hook should stop the adapter
    assert adapter.stopped is True
