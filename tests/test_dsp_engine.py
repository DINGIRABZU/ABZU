import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import dsp_engine


def test_pitch_shift_calls_ffmpeg(monkeypatch):
    data = np.zeros(10, dtype=np.float32)
    called = {}

    def fake_filter(d, sr, filt):
        called['filt'] = filt
        return d * 0 + 1, sr

    monkeypatch.setattr(dsp_engine, '_apply_ffmpeg_filter', fake_filter)
    out, sr = dsp_engine.pitch_shift(data, 44100, 2.0)
    assert sr == 44100
    assert called['filt'].startswith('asetrate=')
    assert np.all(out == 1)


def test_time_stretch_calls_ffmpeg(monkeypatch):
    data = np.zeros(10, dtype=np.float32)
    called = {}

    def fake_filter(d, sr, filt):
        called['filt'] = filt
        return d + 2, sr

    monkeypatch.setattr(dsp_engine, '_apply_ffmpeg_filter', fake_filter)
    out, sr = dsp_engine.time_stretch(data, 22050, 1.5)
    assert sr == 22050
    assert 'atempo=' in called['filt']
    assert np.all(out == 2)


def test_compress_calls_ffmpeg(monkeypatch):
    data = np.zeros(5, dtype=np.float32)
    called = {}

    def fake_filter(d, sr, filt):
        called['filt'] = filt
        return d - 1, sr

    monkeypatch.setattr(dsp_engine, '_apply_ffmpeg_filter', fake_filter)
    out, sr = dsp_engine.compress(data, 16000)
    assert sr == 16000
    assert 'acompressor' in called['filt']
    assert np.all(out == -1)


def test_optional_functions_raise(monkeypatch):
    if dsp_engine.rave is not None:
        monkeypatch.setattr(dsp_engine, 'rave', None)
    if dsp_engine.torch is not None:
        monkeypatch.setattr(dsp_engine, 'torch', None)
    with pytest.raises(RuntimeError):
        dsp_engine.rave_encode(np.zeros(1), 44100, Path('x'))
    with pytest.raises(RuntimeError):
        dsp_engine.rave_decode(np.zeros(1), 44100, Path('x'))
    with pytest.raises(RuntimeError):
        dsp_engine.rave_morph(np.zeros(1), np.zeros(1), 44100, 0.5, Path('x'))

    if dsp_engine.nsynth_fastgen is not None:
        monkeypatch.setattr(dsp_engine, 'nsynth_fastgen', None)
    with pytest.raises(RuntimeError):
        dsp_engine.nsynth_interpolate(np.zeros(1), np.zeros(1), 44100, 0.5, Path('x'))
