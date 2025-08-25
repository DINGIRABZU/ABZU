"""Tests for AudioSegment fallback to NpAudioSegment when soundfile is absent."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_numpy_audio_segment_without_soundfile(monkeypatch):
    """AudioSegment uses NumPy backend and supports basic ops without soundfile."""
    # Force numpy backend and reload module
    monkeypatch.setenv("AUDIO_BACKEND", "numpy")
    sys.modules.pop("audio.segment", None)
    segment = importlib.import_module("audio.segment")

    # Simulate missing soundfile dependency
    monkeypatch.setattr(segment, "sf", None)

    # AudioSegment should resolve to the NumPy implementation
    assert segment.AudioSegment is segment.NpAudioSegment

    # Create simple stereo segments
    data1 = np.zeros((1000, 2), dtype=np.float32)
    data2 = np.ones((500, 2), dtype=np.float32)
    seg1 = segment.AudioSegment(data1, 8000)
    seg2 = segment.AudioSegment(data2, 8000)

    # Basic operations should execute without errors on NumPy arrays
    result = seg1.apply_gain(-3)
    result = result.pan(-0.5)
    result = result.overlay(seg2, position=100)
    result = result.fade_in(50)
    result = result.fade_out(50)
    result = result.reverse()
    sliced = result[0:10]

    assert isinstance(sliced, segment.NpAudioSegment)
    assert isinstance(sliced.data, np.ndarray)
