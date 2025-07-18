import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import training_guide


def test_log_result_json_and_db(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(training_guide, 'FEEDBACK_FILE', tmp_path / 'feed.json')

    def fake_log(emotion, sat, align, clear, db_path=training_guide.db_storage.DB_PATH):
        calls.append((emotion, sat, align, clear))

    monkeypatch.setattr(training_guide.db_storage, 'log_feedback', fake_log)

    intent = {'intent': 'open', 'action': 'gateway.open'}
    training_guide.log_result(intent, True, 'joy', {'text': 'open sesame'})

    data = json.loads((tmp_path / 'feed.json').read_text())
    assert isinstance(data, list) and data
    assert data[0]['intent'] == 'open'
    assert data[0]['success'] is True
    assert 'response_quality' in data[0] and 'memory_overlap' in data[0]
    assert calls == [('joy', 1.0, 1.0, 1.0)]


def test_evaluate_action_metrics(monkeypatch):
    def fake_load(limit=None):
        return [{'input': 'hello world'}]

    mod = types.SimpleNamespace(load_interactions=fake_load)
    monkeypatch.setitem(sys.modules, 'corpus_memory_logging', mod)

    out = training_guide.evaluate_action({'intent': 'hello'}, {'text': 'hello there'})
    assert set(out) == {'response_quality', 'memory_overlap'}
