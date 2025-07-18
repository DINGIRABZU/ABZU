import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))
sys.modules.setdefault("bark", types.ModuleType("bark"))
sys.modules.setdefault("tortoise", types.ModuleType("tortoise"))
sys.modules.setdefault("tortoise.api", types.ModuleType("tortoise.api"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))

from INANNA_AI import speaking_engine, tts_coqui, tts_tortoise, tts_bark, tts_xtts


def _test_backend(monkeypatch, name, module, attr):
    monkeypatch.setenv("CROWN_TTS_BACKEND", name)
    called = {}
    def fake(text: str, emotion: str) -> str:
        called["args"] = (text, emotion)
        return f"{name}.wav"

    monkeypatch.setattr(module, attr, fake)

    def gtts_fake(*a, **k):
        called["gtts"] = True
        return "gtts.wav"

    monkeypatch.setattr(speaking_engine, "_synthesize_gtts", gtts_fake)
    path = speaking_engine.synthesize_speech("hello", "joy")
    assert path == f"{name}.wav"
    assert called.get("args") == ("hello", "joy")
    assert "gtts" not in called
    monkeypatch.delenv("CROWN_TTS_BACKEND", raising=False)


def test_backend_selection(monkeypatch):
    _test_backend(monkeypatch, "coqui", tts_coqui, "synthesize_speech")
    _test_backend(monkeypatch, "tortoise", tts_tortoise, "synthesize")
    _test_backend(monkeypatch, "bark", tts_bark, "synthesize")
    _test_backend(monkeypatch, "xtts", tts_xtts, "synthesize")


def test_default_falls_back(monkeypatch):
    called = {}
    def gtts_fake(*a, **k):
        called["gtts"] = True
        return "gtts.wav"

    monkeypatch.setattr(speaking_engine, "_synthesize_gtts", gtts_fake)
    path = speaking_engine.synthesize_speech("hi", "calm")
    assert path == "gtts.wav"
    assert called.get("gtts") is True
