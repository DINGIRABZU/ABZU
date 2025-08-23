"""Regression tests for media.audio package."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

pytest.importorskip("omegaconf")

from src.media.audio import generate_waveform, play_waveform


def test_generate_waveform_missing_pydub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure informative error when ``pydub`` is unavailable."""
    monkeypatch.setitem(sys.modules, "pydub", None)
    with pytest.raises(ImportError, match="pydub is required"):
        generate_waveform(1000)


def test_generate_waveform_invokes_pydub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generation should delegate to ``AudioSegment.sine``."""
    fake_segment = object()
    audio_segment = mock.Mock()
    audio_segment.sine.return_value = fake_segment
    monkeypatch.setitem(sys.modules, "pydub", mock.Mock(AudioSegment=audio_segment))
    assert generate_waveform(1000) is fake_segment
    audio_segment.sine.assert_called_once_with(duration=1000, frequency=440)


def test_play_waveform_missing_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure informative error when ``ffmpeg`` is unavailable."""
    monkeypatch.setitem(sys.modules, "ffmpeg", None)
    with pytest.raises(ImportError, match="ffmpeg-python is required"):
        play_waveform(Path("a.wav"))


def test_play_waveform_invokes_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Playback should call into ffmpeg pipeline."""
    ffmpeg_mock = mock.Mock()
    ffmpeg_mock.input.return_value = "in"
    ffmpeg_mock.output.return_value = "out"
    monkeypatch.setitem(sys.modules, "ffmpeg", ffmpeg_mock)
    play_waveform(Path("a.wav"))
    ffmpeg_mock.input.assert_called_once_with("a.wav")
    ffmpeg_mock.output.assert_called_once_with("in", "pipe:", format="wav")
    ffmpeg_mock.run.assert_called_once_with("out", quiet=True)
