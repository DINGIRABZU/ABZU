from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import training_guide


def test_log_result_writes_json_and_db(tmp_path, monkeypatch):
    entries = []
    monkeypatch.setattr(training_guide, "FEEDBACK_FILE", tmp_path / "f.json")

    def fake_log(emotion, sat, align, clear, db_path=training_guide.db_storage.DB_PATH):
        entries.append((emotion, sat, align, clear))

    monkeypatch.setattr(training_guide.db_storage, "log_feedback", fake_log)

    intent = {"intent": "open", "action": "gateway.open"}
    training_guide.log_result(intent, True, "joy", {"text": "open"})
    training_guide.log_result(intent, False, None, {"text": "fail"})

    data = json.loads((tmp_path / "f.json").read_text())
    assert len(data) == 2
    assert data[0]["success"] is True
    assert data[1]["tone"] is None
    assert "response_quality" in data[0] and "memory_overlap" in data[0]
    assert entries == [("joy", 1.0, 1.0, 1.0), ("neutral", 0.0, 0.0, 0.0)]
