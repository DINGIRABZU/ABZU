"""Tests for logging sample interactions to JSONL."""

from __future__ import annotations

import json

import corpus_memory_logging as cml


def test_append_and_parse_json_lines(tmp_path, monkeypatch):
    interactions = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", interactions)

    cml.log_interaction("hello", {"intent": "greet"}, {}, "ok")
    cml.log_interaction("bye", {"intent": "farewell"}, {}, "done")

    lines = interactions.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    records = [json.loads(line) for line in lines]
    assert records[0]["input"] == "hello"
    assert records[1]["outcome"] == "done"

    loaded = cml.load_interactions()
    assert loaded == records


def test_ritual_result_logging(tmp_path, monkeypatch):
    interactions = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", interactions)

    cml.log_ritual_result("dance", ["step1", "step2"])

    line = interactions.read_text(encoding="utf-8").strip()
    record = json.loads(line)
    assert record["ritual"] == "dance"
    assert record["steps"] == ["step1", "step2"]

    entries = cml.load_interactions()
    assert entries[0]["ritual"] == "dance"
