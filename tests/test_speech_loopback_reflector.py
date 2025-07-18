import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types

# stub heavy optional dependencies before importing the module
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)

from INANNA_AI import speech_loopback_reflector


def test_reflect_updates_voice(monkeypatch, tmp_path):
    dummy = tmp_path / "x.wav"
    dummy.write_bytes(b"data")

    info = {"emotion": "joy", "arousal": 0.6, "valence": 0.7}
    monkeypatch.setattr(
        speech_loopback_reflector.emotion_analysis,
        "analyze_audio_emotion",
        lambda p: info,
    )
    called = {}

    def fake_update(history):
        called["h"] = history

    monkeypatch.setattr(
        speech_loopback_reflector.voice_evolution,
        "update_voice_from_history",
        fake_update,
    )

    result = speech_loopback_reflector.reflect(str(dummy))
    assert result == info
    assert called["h"] == [info]
