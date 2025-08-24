from __future__ import annotations

import numpy as np

from tools import reflection_loop, session_logger


def test_detect_expression():
    joy = np.full((1, 1, 3), 200, dtype=np.uint8)
    sad = np.full((1, 1, 3), 50, dtype=np.uint8)
    neutral = np.full((1, 1, 3), 120, dtype=np.uint8)

    assert reflection_loop.detect_expression(joy) == "joy"
    assert reflection_loop.detect_expression(sad) == "sadness"
    assert reflection_loop.detect_expression(neutral) == "neutral"


def test_session_logger(tmp_path, monkeypatch):
    monkeypatch.setattr(session_logger, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(session_logger, "VIDEO_DIR", tmp_path / "video")
    monkeypatch.setattr(session_logger, "imageio", None)
    monkeypatch.setattr(session_logger, "np", None)

    audio_in = tmp_path / "in.wav"
    audio_in.write_text("data")
    out_audio = session_logger.log_audio(audio_in)
    assert out_audio.exists()

    out_video = session_logger.log_video([[0]])
    assert out_video.exists()
