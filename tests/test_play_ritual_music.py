"""Tests for play ritual music."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))

import audio.play_ritual_music as prm


def test_play_ritual_music_cli(tmp_path, monkeypatch):
    def dummy_compose(
        tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"
    ):
        wave = np.zeros(100, dtype=np.float32)
        if wav_path:
            sf.write(wav_path, wave, sample_rate)
        return wave

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )
    class DummyBackend:
        def play(self, path: Path, wave: np.ndarray, sample_rate: int = 44100) -> None:
            prm.backends._write_wav(path, wave, sample_rate)

    monkeypatch.setattr(prm.backends, "get_backend", lambda: DummyBackend())

    out = tmp_path / "ritual.wav"
    prm.main(["--emotion", "joy", "--ritual", "\u2609", "--output", str(out)])

    assert out.exists()


def test_play_ritual_music_fallback(tmp_path, monkeypatch):
    def dummy_compose(
        tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"
    ):
        return np.zeros(100, dtype=np.float32)

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )

    called = {}

    class DummyBackend:
        def play(self, path: Path, wave: np.ndarray, sample_rate: int = 44100) -> None:
            called["sample_rate"] = sample_rate
            prm.backends._write_wav(path, wave, sample_rate)

    monkeypatch.setattr(prm.backends, "get_backend", lambda: DummyBackend())

    out = prm.compose_ritual_music(
        "joy", "\u2609", output_dir=tmp_path, sample_rate=8000
    )

    assert out.exists()
    assert out == tmp_path / "ritual.wav"
    assert called["sample_rate"] == 8000
