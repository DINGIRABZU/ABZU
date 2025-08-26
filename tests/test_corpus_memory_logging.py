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
    monkeypatch.setattr(cml, "MAX_LOG_SIZE", 50)

    # pre-populate with valid JSON lines that exceed MAX_LOG_SIZE
    entry = json.dumps({"x": "y" * 20})
    interactions.write_text(entry + "\n" + entry + "\n", encoding="utf-8")

    # this write should trigger a rotation and start a fresh log
    cml.log_interaction("hi", {"emotion": "joy"}, {"emotion": "joy"}, "success")

    rotated = list(tmp_path.glob("interactions-*.jsonl"))
    assert len(rotated) == 1

    # rotated file preserves JSONL integrity
    rotated_lines = rotated[0].read_text().splitlines()
    assert all(json.loads(line) for line in rotated_lines)

    # current log contains only the new entry
    assert interactions.exists()
    current_lines = interactions.read_text().splitlines()
    assert len(current_lines) == 1
    assert json.loads(current_lines[0])["input"] == "hi"
