import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# provide lightweight stubs for optional heavy modules
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))
sys.modules.setdefault("yaml", types.ModuleType("yaml"))
sys.modules["yaml"].safe_load = lambda s: {}

from INANNA_AI import emotional_synaptic_engine as ese


def test_emotion_filter_mappings():
    joy = ese.map_emotion_to_filters("joy")
    calm = ese.map_emotion_to_filters("calm")
    fear = ese.map_emotion_to_filters("fear")

    assert joy["timbre"] == "bright"
    assert calm["timbre"] == "soft"
    assert fear["timbre"] == "tense"

    for params in (joy, calm, fear):
        assert "pitch" in params and "speed" in params

