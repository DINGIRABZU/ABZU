import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archetype_shift_engine as ase
import emotion_registry


def test_calm_high_resonance_triggers_citrinitas(monkeypatch):
    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: 0.85)
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: "rubedo_layer")
    layer = ase.maybe_shift_archetype("greeting", "calm")
    assert layer == "citrinitas_layer"
