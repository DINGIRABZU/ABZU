"""Audit logging for operator commands."""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from typing import Any, Callable, Dict

import operator_api


@pytest.fixture
def client(tmp_path: Path, monkeypatch: MonkeyPatch) -> TestClient:
    app = FastAPI()
    app.include_router(operator_api.router)
    monkeypatch.chdir(tmp_path)
    operator_api._event_clients.clear()
    with TestClient(app) as c:
        yield c


def test_command_audit_log(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    def dispatch(
        operator: str,
        agent: str,
        func: Callable[..., Dict[str, str]],
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, str]:
        return {"ack": "noop"}

    monkeypatch.setattr(operator_api._dispatcher, "dispatch", dispatch)

    resp = client.post(
        "/operator/command",
        json={"operator": "overlord", "agent": "crown", "command": "noop"},
    )
    assert resp.status_code == 200
    cid = resp.json()["command_id"]

    log_path = Path("logs") / "operator_commands.jsonl"
    assert log_path.exists()
    entry = json.loads(log_path.read_text().splitlines()[-1])
    assert entry["command_id"] == cid
    assert entry["agent"] == "crown"
    assert entry["result"] == {"ack": "noop"}
    assert "started_at" in entry and "completed_at" in entry
