import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import sonic_emotion_mapper as sem


def test_map_emotion_to_sound_rubedo():
    data = sem.map_emotion_to_sound("joy", "Rubedo")
    assert data["tempo"] == 140
    assert data["scale"] == "A_major"
    assert "trumpet" in data["timbre"]
    assert data["harmonics"] == "bright_major"
    assert set(data["qnl"]) == {"melody", "rhythm", "harmonics", "ambient"}


def test_map_emotion_to_sound_defaults():
    data = sem.map_emotion_to_sound("unknown", "Albedo")
    assert data["tempo"] == 100
    assert data["scale"] == "F_major"
    assert data["timbre"] == ["flute", "violin"]
    assert data["harmonics"] == "balanced_chords"


