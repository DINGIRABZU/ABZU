import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))

from INANNA_AI import voice_evolution, voice_layer_albedo


def test_load_voice_config(tmp_path, monkeypatch):
    cfg = tmp_path / "voice_config.yaml"
    cfg.write_text("Sage:\n  pitch: 0.1\n  speed: 1.2\n  tone: lunar\n")
    importlib.reload(voice_evolution)
    voice_evolution.VOICE_CONFIG = voice_evolution.load_voice_config(cfg)
    for info in voice_evolution.VOICE_CONFIG.values():
        tone = info.get("tone")
        if tone:
            voice_evolution.DEFAULT_VOICE_STYLES[tone] = {
                "speed": float(info.get("speed", 1.0)),
                "pitch": float(info.get("pitch", 0.0)),
            }
    assert voice_evolution.VOICE_CONFIG["sage"]["tone"] == "lunar"
    assert voice_evolution.DEFAULT_VOICE_STYLES["lunar"]["speed"] == 1.2


def test_modulate_voice_uses_config(tmp_path, monkeypatch):
    cfg = tmp_path / "voice_config.yaml"
    cfg.write_text("Sage:\n  pitch: 0.2\n  speed: 0.8\n  tone: lunar\n")
    importlib.reload(voice_evolution)
    voice_evolution.VOICE_CONFIG = voice_evolution.load_voice_config(cfg)
    for info in voice_evolution.VOICE_CONFIG.values():
        tone = info.get("tone")
        if tone:
            voice_evolution.DEFAULT_VOICE_STYLES[tone] = {
                "speed": float(info.get("speed", 1.0)),
                "pitch": float(info.get("pitch", 0.0)),
            }
    monkeypatch.setattr(
        voice_layer_albedo, "TONE_PRESETS", voice_layer_albedo.TONE_PRESETS.copy()
    )
    monkeypatch.setattr(
        voice_layer_albedo, "voice_evolution", voice_evolution
    )
    importlib.reload(voice_layer_albedo)

    called = {}

    def fake_synth(text: str, tone: str):
        called["args"] = (text, tone)
        return "x.wav"

    monkeypatch.setattr(voice_layer_albedo.speaking_engine, "synthesize_speech", fake_synth)

    path = voice_layer_albedo.modulate_voice("hi", "sage")
    assert path == "x.wav"
    assert called["args"] == ("hi", "lunar")
    assert voice_evolution.DEFAULT_VOICE_STYLES["lunar"]["pitch"] == 0.2

