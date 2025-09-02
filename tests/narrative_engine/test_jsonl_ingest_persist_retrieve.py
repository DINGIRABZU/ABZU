"""Tests for jsonl ingest persist retrieve."""

from pathlib import Path

from memory import narrative_engine
from scripts.ingest_biosignals_jsonl import ingest_file

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"

__version__ = "0.1.0"


def test_jsonl_ingest_persist_retrieve(tmp_path, monkeypatch):
    """JSONL rows are ingested, stored, and retrievable."""
    db_path = tmp_path / "stories.db"
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)
    jsonl_path = DATA_DIR / "sample_biosignals_anonymized.jsonl"
    ingest_file(jsonl_path)
    events = list(narrative_engine.query_events())
    assert [e["payload"]["action"] for e in events] == [
        "calm",
        "elevated heart rate",
        "calm",
    ]
