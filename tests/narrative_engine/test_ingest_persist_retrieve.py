"""Tests for ingest persist retrieve."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import narrative_api
from memory import narrative_engine
from scripts.ingest_biosignals import ingest_file

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"

__version__ = "0.2.0"


def test_ingest_persist_retrieve(tmp_path, monkeypatch):
    """CSV rows are ingested, persisted, and retrievable via the API."""

    db_path = tmp_path / "stories.db"
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)
    csv_path = DATA_DIR / "sample_biosignals.csv"
    ingest_file(csv_path)

    app = FastAPI()
    app.include_router(narrative_api.router)
    client = TestClient(app)

    res = client.get("/story/log")
    assert res.json() == {
        "stories": ["calm", "elevated heart rate", "calm"],
    }

    res = client.get("/story/stream")
    lines = [json.loads(line) for line in res.text.strip().splitlines()]
    assert lines == [
        {"story": "calm"},
        {"story": "elevated heart rate"},
        {"story": "calm"},
    ]

    client.post("/story", json={"text": "rest"})
    res = client.get("/story/log")
    assert res.json()["stories"][-1] == "rest"
