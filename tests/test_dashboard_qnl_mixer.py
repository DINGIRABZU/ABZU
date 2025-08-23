"""Tests for dashboard qnl mixer."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest


def _app_path() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "dashboard" / "qnl_mixer.py"


def test_qnl_mixer_processes_audio(monkeypatch):
    fake_librosa = types.SimpleNamespace(
        load=lambda f, sr=44100, mono=True: (np.zeros(4), sr),
        stft=lambda data: np.ones((2, 2)),
        amplitude_to_db=lambda spec, ref=np.max: spec,
        display=types.SimpleNamespace(specshow=lambda *a, **k: None),
    )
    fake_sf = types.SimpleNamespace(
        write=lambda buf, data, sr, format="WAV": buf.write(b"data")
    )
    fake_mix = types.SimpleNamespace(
        apply_audio_params=lambda data, sr, pitch, tempo, cutoff: data,
        embedding_to_params=lambda emb: (0, 0, 0),
    )
    fake_qnl = types.SimpleNamespace(quantum_embed=lambda text: np.zeros(3))

    monkeypatch.setitem(sys.modules, "librosa", fake_librosa)
    monkeypatch.setitem(sys.modules, "librosa.display", fake_librosa.display)
    monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
    monkeypatch.setitem(sys.modules, "audio.mix_tracks", fake_mix)
    monkeypatch.setitem(sys.modules, "MUSIC_FOUNDATION.qnl_utils", fake_qnl)

    at = AppTest.from_file(_app_path())
    at.run()
    at.file_uploader[0].upload(b"00", "test.wav")
    at.text_input[0].set_value("qnl")
    at.run(timeout=10)

    assert at.audio, "audio widget should be rendered"
