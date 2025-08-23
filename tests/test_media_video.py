"""Regression tests for media.video package."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

from src.media.video import generate_video, play_video


def test_generate_video_missing_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure informative error when ``ffmpeg`` is unavailable."""
    monkeypatch.setitem(sys.modules, "ffmpeg", None)
    with pytest.raises(ImportError, match="ffmpeg-python is required"):
        generate_video([], Path("out.mp4"))


def test_generate_video_invokes_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generation should configure ffmpeg pipeline."""
    ffmpeg_mock = mock.Mock()
    ffmpeg_mock.input.return_value = "in"
    ffmpeg_mock.output.return_value = "out"
    monkeypatch.setitem(sys.modules, "ffmpeg", ffmpeg_mock)
    generate_video([], Path("out.mp4"))
    ffmpeg_mock.input.assert_called_once_with(
        "pipe:", format="image2", pattern_type="glob", framerate=24
    )
    ffmpeg_mock.output.assert_called_once_with("in", "out.mp4")
    ffmpeg_mock.run.assert_called_once_with("out", quiet=True)


def test_play_video_missing_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure informative error when ``ffmpeg`` is unavailable."""
    monkeypatch.setitem(sys.modules, "ffmpeg", None)
    with pytest.raises(ImportError, match="ffmpeg-python is required"):
        play_video(Path("out.mp4"))


def test_play_video_invokes_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Playback should call into ffmpeg pipeline."""
    ffmpeg_mock = mock.Mock()
    ffmpeg_mock.input.return_value = "in"
    monkeypatch.setitem(sys.modules, "ffmpeg", ffmpeg_mock)
    play_video(Path("out.mp4"))
    ffmpeg_mock.input.assert_called_once_with("out.mp4")
    ffmpeg_mock.run.assert_called_once_with("in", quiet=True)
