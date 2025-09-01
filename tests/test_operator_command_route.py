import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import operator_api


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    app = FastAPI()
    app.include_router(operator_api.router)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs" / "operators").mkdir(parents=True)
    with TestClient(app) as c:
        yield c


def test_crown_routes_to_razar(client: TestClient) -> None:
    resp = client.post(
        "/operator/command",
        json={"operator": "crown", "agent": "razar", "command": "status"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"result": {"ack": "status"}}
    log_path = Path("logs/operators/crown.log")
    assert log_path.exists()
    record = json.loads(log_path.read_text().splitlines()[-1])
    assert record["agent"] == "razar"
    assert record["command"] == "_noop"
