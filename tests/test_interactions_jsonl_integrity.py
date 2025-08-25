"""Additional JSONL integrity tests for interaction logging."""

from __future__ import annotations

import json
import logging

import corpus_memory_logging as cml


def test_log_interaction_with_metadata(tmp_path, monkeypatch):
    interactions = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", interactions)

    cml.log_interaction(
        "hi",
        {"intent": "greet"},
        {"emotion": "joy"},
        "ok",
        source_type="unit",
        genre="rock",
        instrument="guitar",
        feedback="great",
        rating=4.2,
    )

    data = interactions.read_text(encoding="utf-8")
    assert data.endswith("\n")
    record = json.loads(data.strip())
    assert record["genre"] == "rock"
    assert record["instrument"] == "guitar"
    assert record["feedback"] == "great"
    assert record["rating"] == 4.2

    loaded = cml.load_interactions()
    assert loaded == [record]


def test_load_interactions_skips_invalid_json_and_limit(tmp_path, monkeypatch, caplog):
    interactions = tmp_path / "interactions.jsonl"
    interactions.write_text(
        '{"input":"a"}\nnot json\n{"input":"b"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", interactions)

    with caplog.at_level(logging.ERROR):
        records = cml.load_interactions()
    assert len(records) == 2
    assert records[0]["input"] == "a"
    assert records[1]["input"] == "b"
    assert "invalid json line" in caplog.text.lower()

    limited = cml.load_interactions(limit=1)
    assert limited == [records[1]]
