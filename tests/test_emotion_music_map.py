import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
dummy_yaml = types.ModuleType("yaml")
dummy_yaml.safe_load = lambda s: {}
sys.modules.setdefault("yaml", dummy_yaml)

from MUSIC_FOUNDATION import inanna_music_COMPOSER_ai as composer


def test_get_emotion_music_params(monkeypatch):
    mapping = {"joy": {"tempo": 150, "scale": "C_major", "rhythm": "swing"}}
    monkeypatch.setattr(composer.emotional_state, "get_last_emotion", lambda: "joy")

    tempo, scale, melody, rhythm = composer.get_emotion_music_params(120, mapping)
    assert tempo == 150
    assert scale == "C_major"
    assert rhythm == "swing"
    assert melody == composer.SCALE_MELODIES["C_major"]
