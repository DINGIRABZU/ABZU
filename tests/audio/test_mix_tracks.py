from pathlib import Path

import numpy as np
import pytest

from src.audio import mix_tracks

__version__ = "0.0.0"


def test_apply_dsp(monkeypatch):
    data = np.array([1.0, 2.0])

    def fake_pitch(d, sr, amt):
        return d + amt, sr

    def fake_time(d, sr, amt):
        return d * amt, sr

    def fake_comp(d, sr, thresh, ratio):
        return d + ratio, sr

    monkeypatch.setattr(mix_tracks.dsp_engine, "pitch_shift", fake_pitch)
    monkeypatch.setattr(mix_tracks.dsp_engine, "time_stretch", fake_time)
    monkeypatch.setattr(mix_tracks.dsp_engine, "compress", fake_comp)
    out, sr = mix_tracks._apply_dsp(
        data, 44100, {"pitch": 1, "time": 2, "compress": {"ratio": 3}}
    )
    np.testing.assert_allclose(out, ((data + 1) * 2) + 3)
    assert sr == 44100


def test_mix_audio_emotion(monkeypatch):
    a = np.array([0.0, 1.0])
    b = np.array([1.0, 0.0, 1.0])

    def fake_load(path, logger=None):
        return (a if "a" in str(path) else b), 44100

    monkeypatch.setattr(mix_tracks, "_load", fake_load)
    monkeypatch.setattr(
        mix_tracks.audio_ingestion,
        "extract_tempo",
        lambda d, s: 100.0 if d is a else 120.0,
    )
    monkeypatch.setattr(
        mix_tracks.audio_ingestion,
        "extract_key",
        lambda d: "C" if d is a else "G",
    )
    monkeypatch.setattr(
        mix_tracks,
        "_load_emotion_map",
        lambda path=None: {"joy": {"tempo": 90, "scale": "D"}},
    )

    mix, sr, info = mix_tracks.mix_audio([Path("a"), Path("b")], emotion="joy")
    np.testing.assert_allclose(mix, np.array([0.5, 0.5, 0.5]))
    assert sr == 44100
    assert info == {"tempo": 90.0, "key": "D"}


def test_mix_from_instructions(monkeypatch):
    a = np.array([0.0, 1.0])
    b = np.array([1.0, 0.0, 1.0])

    def fake_load(path, logger=None):
        return (a if "a" in str(path) else b), 44100

    def fake_apply(data, sr, params, logger=None):
        return data, sr

    monkeypatch.setattr(mix_tracks, "_load", fake_load)
    monkeypatch.setattr(mix_tracks, "_apply_dsp", fake_apply)
    instr = {"stems": [{"file": "a"}, {"file": "b"}]}
    mix, sr = mix_tracks.mix_from_instructions(instr)
    np.testing.assert_allclose(mix, np.array([0.5, 0.5, 0.5]))
    assert sr == 44100


def test_mix_from_instructions_no_stems():
    with pytest.raises(ValueError):
        mix_tracks.mix_from_instructions({})


def test_mix_audio_rate_mismatch(monkeypatch):
    a = np.array([0.0])
    b = np.array([0.0])

    def fake_load(path, logger=None):
        return (a, 44100) if "a" in str(path) else (b, 48000)

    monkeypatch.setattr(mix_tracks, "_load", fake_load)
    with pytest.raises(ValueError):
        mix_tracks.mix_audio([Path("a"), Path("b")])


def test_mix_from_instructions_rate_mismatch(monkeypatch):
    a = np.array([0.0])
    b = np.array([0.0])

    def fake_load(path, logger=None):
        return (a, 44100) if "a" in str(path) else (b, 48000)

    def fake_apply(data, sr, params, logger=None):
        return data, sr

    monkeypatch.setattr(mix_tracks, "_load", fake_load)
    monkeypatch.setattr(mix_tracks, "_apply_dsp", fake_apply)
    instr = {"stems": [{"file": "a"}, {"file": "b"}]}
    with pytest.raises(ValueError):
        mix_tracks.mix_from_instructions(instr)
