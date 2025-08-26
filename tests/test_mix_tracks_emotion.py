"""Tests for mix tracks emotion."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from audio import mix_tracks


def test_mix_audio_emotion_guides_tempo(monkeypatch):
    monkeypatch.setattr(mix_tracks, "_load", lambda p, logger=None: (np.zeros(10), 44100))
    monkeypatch.setattr(mix_tracks.audio_ingestion, "extract_tempo", lambda d, s: 100.0)
    monkeypatch.setattr(mix_tracks.audio_ingestion, "extract_key", lambda d: "C:maj")

    mix, sr, info = mix_tracks.mix_audio([Path("a.wav"), Path("b.wav")], emotion="joy")
    assert info["tempo"] == 140
    assert info["key"] == "C_major"


def test_mix_audio_averages_analysis(monkeypatch):
    monkeypatch.setattr(mix_tracks, "_load", lambda p, logger=None: (np.zeros(10), 44100))
    tempos = iter([100.0, 120.0])
    monkeypatch.setattr(
        mix_tracks.audio_ingestion, "extract_tempo", lambda d, s: next(tempos)
    )
    monkeypatch.setattr(mix_tracks.audio_ingestion, "extract_key", lambda d: "C:maj")

    mix, sr, info = mix_tracks.mix_audio([Path("a.wav"), Path("b.wav")])
    assert info["tempo"] == 110.0
    assert info["key"] == "C:maj"


def test_load_emotion_map_cached(tmp_path, monkeypatch):
    """Ensure the emotion map YAML is read only once."""

    path = tmp_path / "map.yaml"
    path.write_text("joy: {tempo: 120}")

    calls = {"count": 0}

    def fake_safe_load(f):
        calls["count"] += 1
        return {}

    monkeypatch.setattr(mix_tracks.yaml, "safe_load", lambda f: fake_safe_load(f))
    mix_tracks._load_emotion_map.cache_clear()

    mix_tracks._load_emotion_map(path)
    mix_tracks._load_emotion_map(path)

    assert calls["count"] == 1
