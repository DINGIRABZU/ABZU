"""Ensure biosignal rows transform, persist, and can be retrieved."""

from pathlib import Path

import pytest

from memory import narrative_engine
from scripts.ingest_biosignal_events import ingest_file

__version__ = "0.1.0"

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"


def test_transform_store_retrieve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rows become events in storage and are queryable."""
    db_path = tmp_path / "events.db"
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)
    monkeypatch.setattr(narrative_engine, "CHROMA_DIR", tmp_path)
    csv_path = DATA_DIR / "sample_biosignals_iota.csv"
    ingest_file(csv_path)
    events = list(narrative_engine.query_events(agent_id="sensor"))
    assert [e["payload"]["action"] for e in events] == [
        "calm",
        "elevated heart rate",
        "calm",
    ]
