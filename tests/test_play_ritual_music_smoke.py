"""Smoke test for ritual music playback."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
            sf.write(wav_path, wave, 44100)
        return wave

    monkeypatch.setattr(prm.layer_generators, "compose_human_layer", dummy_compose)

    played: list[Path] = []

    def fake_play_audio(path: Path, loop: bool = False) -> None:
        played.append(Path(path))

    monkeypatch.setattr(prm.expressive_output, "play_audio", fake_play_audio)

    out = tmp_path / "ritual.wav"
    prm.compose_ritual_music("joy", "\u2609", out_path=out)

    assert out.exists()
    assert played and played[0] == out
