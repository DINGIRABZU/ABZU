import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import logging
import corpus_memory_logging as cml


def test_log_and_load(tmp_path, monkeypatch, caplog):
    log_path = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", log_path)

    with caplog.at_level(logging.INFO):
        cml.log_interaction("hello", {"intent": "greet", "emotion": "joy"}, {}, "ok")
        cml.log_interaction("bye", {"intent": "exit"}, {"emotion": "calm"}, "done")

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["input"] == "hello" and first["emotion"] == "joy"

    assert sum(1 for r in caplog.records if r.levelno == logging.INFO and "logged interaction" in r.message) == 2

    all_entries = cml.load_interactions()
    assert len(all_entries) == 2
    assert all_entries[-1]["outcome"] == "done"

    limited = cml.load_interactions(limit=1)
    assert limited == all_entries[-1:]

    # append invalid json to trigger error log
    log_path.write_text(log_path.read_text(encoding="utf-8") + "{\n", encoding="utf-8")
    with caplog.at_level(logging.ERROR):
        entries = cml.load_interactions()
    assert len(entries) == 2
    assert any("invalid json line" in r.message for r in caplog.records)


def test_optional_metadata(tmp_path, monkeypatch):
    log_path = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", log_path)

    cml.log_interaction(
        "play piano",
        {"intent": "music"},
        {},
        "ok",
        source_type="score",
        genre="jazz",
        instrument="piano",
    )

    entry = cml.load_interactions()[0]
    assert entry["source_type"] == "score"
    assert entry["genre"] == "jazz"
    assert entry["instrument"] == "piano"
