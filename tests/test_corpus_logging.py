from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import corpus_memory_logging as cml


def test_log_writes_jsonl(tmp_path, monkeypatch):
    log_path = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", log_path)
    monkeypatch.setattr(cml, "QUARANTINE_FILE", log_path.with_suffix(".quarantine.jsonl"))
    cml.log_interaction("hi", {"intent": "greet"}, {}, "ok")
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["input"] == "hi" and entry["intent"]["intent"] == "greet"


def test_log_rotation(tmp_path, monkeypatch):
    log_path = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(cml, "INTERACTIONS_FILE", log_path)
    monkeypatch.setattr(cml, "QUARANTINE_FILE", log_path.with_suffix(".quarantine.jsonl"))
    monkeypatch.setattr(cml, "MAX_LOG_SIZE", 150)

    cml.log_interaction("a" * 40, {"intent": "x"}, {}, "ok")
    cml.log_interaction("b" * 40, {"intent": "x"}, {}, "ok")

    rotated = list(tmp_path.glob("interactions-*.jsonl"))
    assert rotated and log_path.exists()
    # rotated file should contain first entry
    first = json.loads(rotated[0].read_text(encoding="utf-8").splitlines()[0])
    assert first["input"].startswith("a")
    # current log should contain second entry
    second = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert second["input"].startswith("b")
