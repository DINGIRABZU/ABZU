import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import self_correction_engine


def test_adjust_updates_voice_and_layer(monkeypatch):
    called = {}
    monkeypatch.setattr(
        self_correction_engine.voice_evolution,
        "update_voice_from_history",
        lambda h: called.setdefault("h", h),
    )
    monkeypatch.setattr(
        self_correction_engine.emotional_state,
        "set_current_layer",
        lambda name: called.setdefault("layer", name),
    )

    self_correction_engine.adjust("sad", "joy", 0.3)

    assert called["h"] == [{"emotion": "joy", "arousal": 0.5, "valence": 0.5, "sentiment": 0.0}]
    assert called["layer"] == "joy"


def test_adjust_respects_tolerance(monkeypatch):
    called = {}
    monkeypatch.setattr(
        self_correction_engine.voice_evolution,
        "update_voice_from_history",
        lambda h: called.setdefault("h", h),
    )
    monkeypatch.setattr(
        self_correction_engine.emotional_state,
        "set_current_layer",
        lambda name: called.setdefault("layer", name),
    )

    self_correction_engine.adjust("sad", "joy", 1.5)

    assert "h" not in called
    assert "layer" not in called


def test_archetype_conflict_tunes_voice(monkeypatch):
    entries: list[list[dict]] = []
    monkeypatch.setattr(
        self_correction_engine.voice_evolution,
        "update_voice_from_history",
        lambda h: entries.append(h),
    )
    monkeypatch.setattr(
        self_correction_engine.emotional_state,
        "get_current_layer",
        lambda: "rubedo_layer",
    )
    monkeypatch.setattr(
        self_correction_engine.emotional_state,
        "set_current_layer",
        lambda name: None,
    )

    self_correction_engine.adjust("anger", "joy", 0.3)

    assert [{"emotion": "anger", "arousal": 0.5, "valence": 0.5, "sentiment": 0.0}] in entries

