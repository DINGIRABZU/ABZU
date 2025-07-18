from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import training_guide


def test_auto_retrain_called(tmp_path, monkeypatch):
    feed = tmp_path / "feedback.json"
    insight = tmp_path / "insight.json"
    feed.write_text("[]", encoding="utf-8")
    insight.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(training_guide, "FEEDBACK_FILE", feed)
    monkeypatch.setattr(training_guide.auto_retrain, "INSIGHT_FILE", insight)
    monkeypatch.setattr(training_guide, "AUTO_RETRAIN_THRESHOLD", 1)
    calls = []
    monkeypatch.setattr(training_guide.auto_retrain, "main", lambda args: calls.append(args))
    monkeypatch.setattr(training_guide.db_storage, "log_feedback", lambda *a, **k: None)

    intent = {"intent": "open", "action": "gateway.open"}
    training_guide.log_result(intent, True, "joy", {"text": "open"})

    assert calls == [["--run"]]
