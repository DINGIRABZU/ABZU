"""Regression tests for media.avatar package."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import src.media.avatar as avatar


def test_generate_avatar_pipeline(monkeypatch) -> None:
    """Generation should invoke audio and video pipelines."""
    gen_waveform = mock.Mock(return_value="audio")
    gen_video = mock.Mock()
    monkeypatch.setattr(avatar.generation, "generate_waveform", gen_waveform)
    monkeypatch.setattr(avatar.generation, "generate_video", gen_video)
    result = avatar.generate_avatar(1000, [], Path("video.mp4"))
    assert result == "audio"
    gen_waveform.assert_called_once_with(1000)
    gen_video.assert_called_once_with([], Path("video.mp4"))


def test_play_avatar_pipeline(monkeypatch) -> None:
    """Playback should invoke audio and video playback helpers."""
    play_audio = mock.Mock()
    play_video = mock.Mock()
    monkeypatch.setattr(avatar.playback, "play_waveform", play_audio)
    monkeypatch.setattr(avatar.playback, "play_video", play_video)
    avatar.play_avatar(Path("a.wav"), Path("v.mp4"))
    play_audio.assert_called_once_with(Path("a.wav"))
    play_video.assert_called_once_with(Path("v.mp4"))
