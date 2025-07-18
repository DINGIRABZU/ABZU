import json
import sys
from pathlib import Path
from types import SimpleNamespace
import logging

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import auto_retrain


def test_build_dataset():
    feedback = [
        {"intent": "open", "action": "door", "success": True},
        {"intent": "close", "action": "door", "success": True},
        {"intent": "fail", "action": "door", "success": False},
    ]
    ds = auto_retrain.build_dataset(feedback)
    assert ds == [
        {"prompt": "open", "completion": "door"},
        {"prompt": "close", "completion": "door"},
    ]


def test_main_invokes_api(tmp_path, monkeypatch):
    insight = {}
    feedback = [
        {
            "intent": "open",
            "action": "door",
            "success": True,
            "response_quality": 1.0,
            "memory_overlap": 0.0,
        }
    ]
    ins = tmp_path / "insight.json"
    ins.write_text(json.dumps(insight), encoding="utf-8")
    fb = tmp_path / "feed.json"
    fb.write_text(json.dumps(feedback), encoding="utf-8")
    monkeypatch.setattr(auto_retrain, "INSIGHT_FILE", ins)
    monkeypatch.setattr(auto_retrain, "FEEDBACK_FILE", fb)
    monkeypatch.setattr(auto_retrain, "NOVELTY_THRESHOLD", 0.0)
    monkeypatch.setattr(auto_retrain, "COHERENCE_THRESHOLD", 0.0)
    monkeypatch.setattr(auto_retrain, "system_idle", lambda: True)

    calls = {}

    def fake_ft(data):
        calls["data"] = data

    dummy_api = SimpleNamespace(fine_tune=fake_ft)
    monkeypatch.setitem(sys.modules, "llm_api", dummy_api)

    auto_retrain.main(["--run"])

    assert calls.get("data") == [{"prompt": "open", "completion": "door"}]


def test_load_json_logs_error(tmp_path, caplog):
    missing = tmp_path / "none.json"
    with caplog.at_level(logging.ERROR):
        out = auto_retrain._load_json(missing, {})
    assert out == {}
    assert any("failed to load" in r.message for r in caplog.records)


def test_compute_metrics_logs_error(caplog):
    class Bad:
        def __iter__(self):
            raise ValueError("boom")

    with caplog.at_level(logging.ERROR):
        novelty, coherence = auto_retrain.compute_metrics({}, Bad())
    assert (novelty, coherence) == (0.0, 0.0)
    assert any("failed to compute metrics" in r.message for r in caplog.records)


def test_build_dataset_logs_error(caplog):
    class Bad:
        def __iter__(self):
            raise ValueError("boom")

    with caplog.at_level(logging.ERROR):
        ds = auto_retrain.build_dataset(Bad())
    assert ds == []
    assert any("failed to build dataset" in r.message for r in caplog.records)


def test_trigger_finetune_logs_error(monkeypatch, caplog):
    def fail(data):
        raise RuntimeError("nope")

    dummy_api = SimpleNamespace(fine_tune=fail)
    monkeypatch.setitem(sys.modules, "llm_api", dummy_api)

    with caplog.at_level(logging.ERROR):
        auto_retrain.trigger_finetune([{"prompt": "p", "completion": "c"}])
    assert any("failed to trigger fine-tune" in r.message for r in caplog.records)
