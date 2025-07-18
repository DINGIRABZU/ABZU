import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learning_mutator as lm
import emotion_registry


def _mock_state(monkeypatch, layer, emotion, resonance):
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: layer)
    monkeypatch.setattr(emotion_registry, "get_last_emotion", lambda: emotion)
    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: resonance)


def test_switch_on_dominant_emotion(monkeypatch):
    matrix = {"x": {"counts": {"total": 1, "success": 1}}}
    _mock_state(monkeypatch, None, "anger", 0.9)
    monkeypatch.setattr(lm, "load_intents", lambda path=None: {})
    suggestions = lm.propose_mutations(matrix)
    assert any("nigredo_layer" in s for s in suggestions)


def test_fuse_on_low_scores(monkeypatch):
    matrix = {
        "a": {"counts": {"total": 5, "success": 1}},
        "b": {"counts": {"total": 5, "success": 0}},
    }
    _mock_state(monkeypatch, "rubedo_layer", "neutral", 0.1)
    monkeypatch.setattr(lm, "load_intents", lambda path=None: {})
    suggestions = lm.propose_mutations(matrix)
    assert any("fuse" in s.lower() and "rubedo_layer" in s for s in suggestions)


def test_cli_activate_sets_layer(monkeypatch):
    called = {}
    monkeypatch.setattr(emotion_registry, "set_current_layer", lambda layer: called.setdefault("layer", layer))
    monkeypatch.setattr(lm, "load_insights", lambda path=None: {})
    monkeypatch.setattr(lm, "propose_mutations", lambda d: [])
    argv = sys.argv.copy()
    sys.argv = ["learning_mutator.py", "--activate", "nigredo_layer"]
    try:
        lm.main()
    finally:
        sys.argv = argv
    assert called.get("layer") == "nigredo_layer"
