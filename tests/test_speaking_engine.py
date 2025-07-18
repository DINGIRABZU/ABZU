import sys
import types
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# provide lightweight stubs for heavy optional modules
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))

from INANNA_AI import speaking_engine


def test_synthesize_speech_creates_wav(tmp_path, monkeypatch):
    class DummyTTS:
        def __init__(self, text):
            self.text = text
        def save(self, path):
            Path(path).write_bytes(b"dummy")
    monkeypatch.setattr(speaking_engine, "gTTS", DummyTTS)
    monkeypatch.setattr(speaking_engine, "emotion_to_archetype", lambda e: "Sage")
    monkeypatch.setattr(speaking_engine, "get_voice_params", lambda e: {"speed": 1.0, "pitch": 0.0})
    monkeypatch.setattr(speaking_engine.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(speaking_engine.librosa, "load", lambda *a, **k: (np.zeros(22050), 22050))

    path = speaking_engine.synthesize_speech("hello", "calm")
    assert Path(path).exists()


def test_play_wav(monkeypatch):
    played = {}

    def dummy_load(path, sr=None, mono=True):
        played["loaded"] = path
        return np.zeros(10), 22050

    class DummySD:
        def play(self, wave, sr):
            played["sr"] = sr
        def wait(self):
            played["waited"] = True

    monkeypatch.setattr(speaking_engine, "sd", DummySD())
    monkeypatch.setattr(speaking_engine, "load_audio", dummy_load)

    speaking_engine.play_wav("x.wav")
    assert played["loaded"] == "x.wav"
    assert played["sr"] == 22050
    assert played["waited"]


def test_emotion_modifies_style(tmp_path, monkeypatch):
    """Voice parameters from emotion should be applied when synthesizing."""

    style = {"speed": 1.2, "pitch": 0.5}
    captured = {}

    class DummyTTS:
        def __init__(self, text):
            self.text = text

        def save(self, path):
            Path(path).write_bytes(b"dummy")

    def dummy_apply(wave, sr, params):
        captured["params"] = params
        return wave

    monkeypatch.setattr(speaking_engine, "gTTS", DummyTTS)
    monkeypatch.setattr(speaking_engine, "emotion_to_archetype", lambda e: "Sage")
    monkeypatch.setattr(speaking_engine, "get_voice_params", lambda e: style)
    monkeypatch.setattr(speaking_engine, "_apply_style", dummy_apply)
    monkeypatch.setattr(speaking_engine, "convert_voice", lambda w, sr, timbre: w)
    monkeypatch.setattr(speaking_engine.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(speaking_engine.librosa, "load", lambda *a, **k: (np.zeros(22050), 22050))

    path = speaking_engine.synthesize_speech("hi", "joy")
    assert Path(path).exists()
    assert captured["params"] == style
