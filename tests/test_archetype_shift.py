from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archetype_shift_engine as ase
import emotion_registry


def test_ritual_keyword_triggers_citrinitas(monkeypatch):
    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: 0.5)
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: None)
    layer = ase.maybe_shift_archetype("begin the ritual ☉", "joy")
    assert layer == "citrinitas_layer"


def test_emotional_overload_shift(monkeypatch):
    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: 0.9)
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: "albedo")
    layer = ase.maybe_shift_archetype("hello", "anger")
    assert layer == "nigredo_layer"
