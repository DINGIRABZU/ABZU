"""Smoke test for ritual music playback."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))

import audio.play_ritual_music as prm


def test_compose_and_play(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def dummy_compose(
        tempo: float,
        melody: list[int],
        *,
        wav_path: str | None = None,
        wave_type: str = "sine",
    ) -> np.ndarray:
        wave: np.ndarray = np.zeros(100, dtype=np.float32)
        if wav_path:
            prm.backends._write_wav(Path(wav_path), wave, 44100)
        return wave

    monkeypatch.setattr(
        prm.waveform.layer_generators, "compose_human_layer", dummy_compose
    )
    monkeypatch.setattr(prm.backends, "sf", None)
    monkeypatch.setattr(prm.backends, "sa", None)
    monkeypatch.setattr(prm.waveform, "sf", object())

    played: list[Path] = []

    def record_play(
        self, path: Path, wave: np.ndarray, sample_rate: int = 44100
    ) -> None:
        played.append(Path(path))
        prm.backends._write_wav(path, wave, sample_rate)

    monkeypatch.setattr(prm.backends.NoOpBackend, "play", record_play)

    out = prm.compose_ritual_music(
        "joy", "\u2609", output_dir=tmp_path, sample_rate=22050
    )

    assert out.exists()
    assert played and played[0] == out
