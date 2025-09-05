import json
from pathlib import Path

import sys
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import operator_api

sys.modules.setdefault(
    "vanna",
    SimpleNamespace(
        __stub__=True,
        train=lambda *a, **k: None,
        connect_to_sqlite=lambda *a, **k: None,
        ask=lambda prompt: ("", None),
    ),
)
import nlq_api


@pytest.fixture
def client(tmp_path, monkeypatch):
    app = FastAPI()
    app.include_router(operator_api.router)
    app.include_router(nlq_api.router)
    monkeypatch.chdir(tmp_path)
    operator_api._event_clients.clear()
    with TestClient(app) as c:
        yield c


def _write_logs():
    path = Path("logs") / "agent_interactions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {"source": "crown", "target": "albedo", "text": "one"},
        {"source": "albedo", "target": "crown", "text": "two"},
        {"source": "crown", "target": "crown", "text": "three"},
    ]
    with path.open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    return entries


def test_conversation_log_pagination(client):
    _write_logs()
    resp = client.get("/conversation/logs", params={"agent": "crown", "limit": 2})
    assert resp.status_code == 200
    logs = resp.json()["logs"]
    assert [e["text"] for e in logs] == ["two", "three"]


def test_nlq_logs_returns_rows(client, monkeypatch):
    monkeypatch.setattr(nlq_api, "query_logs", lambda prompt, db_path=None: [{"x": 1}])
    resp = client.post("/nlq/logs", json={"query": "anything"})
    assert resp.status_code == 200
    assert resp.json() == {"rows": [{"x": 1}]}
