from pathlib import Path

from memory import narrative_engine
from scripts.ingest_biosignals import ingest_file

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"

__version__ = "0.1.0"


def test_ingest_persist_retrieve(tmp_path, monkeypatch):
    """CSV rows are ingested, persisted, and retrievable."""
    db_path = tmp_path / "stories.db"
    monkeypatch.setattr(narrative_engine, "DB_PATH", db_path)
    csv_path = DATA_DIR / "sample_biosignals.csv"
    ingest_file(csv_path)
    assert list(narrative_engine.stream_stories()) == [
        "calm",
        "elevated heart rate",
        "calm",
    ]
