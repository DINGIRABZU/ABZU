"""Tests for auto retrain."""

from __future__ import annotations

import json
import logging
import sys
import types
from pathlib import Path
from types import SimpleNamespace

from tests.helpers.config_stub import build_settings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

config = types.ModuleType("config")
config.settings = build_settings()
sys.modules.setdefault("config", config)

import auto_retrain


def test_build_dataset_includes_mutations(monkeypatch):
    feedback = [
        {"intent": "open", "action": "door", "success": True},
    ]
    monkeypatch.setattr(auto_retrain, "propose_mutations", lambda _ins: ["Patch A"])
    monkeypatch.setattr(auto_retrain, "_load_json", lambda *a, **k: {})
    ds = auto_retrain.build_dataset(feedback)
    assert ds == [
        {"prompt": "open", "completion": "door"},
        {"prompt": "PATCH", "completion": "Patch A"},
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
    monkeypatch.setattr(auto_retrain.feedback_logging, "LOG_FILE", fb)
    monkeypatch.setattr(auto_retrain, "NOVELTY_THRESHOLD", 0.0)
    monkeypatch.setattr(auto_retrain, "COHERENCE_THRESHOLD", 0.0)
    monkeypatch.setattr(auto_retrain, "system_idle", lambda: True)
    monkeypatch.setattr(auto_retrain, "_load_vector_logs", lambda: [{}])

    calls = {}

    def fake_ft(data):
        calls["data"] = data

    dummy_api = SimpleNamespace(fine_tune=fake_ft)
    monkeypatch.setitem(sys.modules, "llm_api", dummy_api)
    monkeypatch.setattr(auto_retrain, "verify_signature", lambda ds: True)
    monkeypatch.setattr(auto_retrain, "propose_mutations", lambda _ins: [])

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


def test_trigger_finetune_aborts_on_bad_signature(monkeypatch):
    calls = {}
    dummy_api = SimpleNamespace(
        fine_tune=lambda data: calls.setdefault("ft", True),
        rollback=lambda: calls.setdefault("rb", True),
    )
    monkeypatch.setitem(sys.modules, "llm_api", dummy_api)
    monkeypatch.setattr(auto_retrain, "verify_signature", lambda ds: False)

    auto_retrain.trigger_finetune([{"prompt": "p", "completion": "c"}])
    assert "ft" not in calls


def test_trigger_finetune_rolls_back_on_failure(monkeypatch, caplog):
    calls = {}

    def fail(data):
        calls["ft"] = True
        raise RuntimeError("nope")

    def rb():
        calls["rb"] = True

    dummy_api = SimpleNamespace(fine_tune=fail, rollback=rb)
    monkeypatch.setitem(sys.modules, "llm_api", dummy_api)
    monkeypatch.setattr(auto_retrain, "verify_signature", lambda ds: True)

    with caplog.at_level(logging.ERROR):
        auto_retrain.trigger_finetune([{"prompt": "p", "completion": "c"}])

    assert calls == {"ft": True, "rb": True}
    assert any("failed to trigger fine-tune" in r.message for r in caplog.records)
