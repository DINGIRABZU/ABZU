import json

import corpus_memory_logging as cml


def test_watchdog_quarantines_bad_lines(tmp_path, monkeypatch):
    interactions = tmp_path / "interactions.jsonl"
    quarantine = tmp_path / "interactions.quarantine.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", interactions)
    monkeypatch.setattr(cml, "QUARANTINE_FILE", quarantine)

    interactions.write_text('{"a": 1}\nnot json\n{"b": 2}\n', encoding="utf-8")

    cml.watchdog()

    lines = interactions.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"a": 1}
    assert json.loads(lines[1]) == {"b": 2}
    assert quarantine.read_text() == "not json\n"


def test_log_rotation(tmp_path, monkeypatch):
    interactions = tmp_path / "interactions.jsonl"
    quarantine = tmp_path / "interactions.quarantine.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", interactions)
    monkeypatch.setattr(cml, "QUARANTINE_FILE", quarantine)
    monkeypatch.setattr(cml, "MAX_LOG_SIZE", 100)

    interactions.write_text("x" * 120, encoding="utf-8")

    cml.log_interaction("hi", {"emotion": "joy"}, {"emotion": "joy"}, "success")

    rotated = list(tmp_path.glob("interactions-*.jsonl"))
    assert len(rotated) == 1
    assert interactions.exists()
    entries = cml.load_interactions()
    assert len(entries) == 1
    assert entries[0]["input"] == "hi"
