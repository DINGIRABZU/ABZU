"""Tests for autoretrain full."""

from __future__ import annotations

import json
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


def test_main_triggers_finetune(tmp_path, monkeypatch):
    insight = {"open": {}}
    feedback = [
        {"intent": "open", "action": "door", "success": True, "response_quality": 0.9},
        {"intent": "close", "action": "door", "success": True, "response_quality": 0.8},
    ]

    ins = tmp_path / "insight.json"
    ins.write_text(json.dumps(insight), encoding="utf-8")
    fb = tmp_path / "feedback.json"
    fb.write_text(json.dumps(feedback), encoding="utf-8")

    monkeypatch.setattr(auto_retrain, "INSIGHT_FILE", ins)
    monkeypatch.setattr(auto_retrain.feedback_logging, "LOG_FILE", fb)
    monkeypatch.setattr(auto_retrain, "NOVELTY_THRESHOLD", 0.3)
    monkeypatch.setattr(auto_retrain, "COHERENCE_THRESHOLD", 0.7)
    monkeypatch.setattr(auto_retrain, "system_idle", lambda: True)
    monkeypatch.setattr(auto_retrain, "_load_vector_logs", lambda: [{}])
    monkeypatch.setattr(auto_retrain, "verify_signature", lambda ds: True)
    monkeypatch.setattr(auto_retrain, "propose_mutations", lambda _ins: [])

    captured = {}

    def fake_ft(data):
        captured["data"] = data

    dummy_api = SimpleNamespace(fine_tune=fake_ft)
    monkeypatch.setitem(sys.modules, "llm_api", dummy_api)

    auto_retrain.main(["--run"])

    expected = [
        {"prompt": "open", "completion": "door"},
        {"prompt": "close", "completion": "door"},
    ]
    assert captured.get("data") == expected
