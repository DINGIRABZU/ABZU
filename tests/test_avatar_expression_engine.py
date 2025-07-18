import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import avatar_expression_engine as aee
from core import video_engine
import audio_engine
import emotional_state


def test_stream_avatar_audio(monkeypatch):
    frames = [np.zeros((4, 4, 3), dtype=np.uint8) for _ in range(2)]
    monkeypatch.setattr(video_engine, "start_stream", lambda: iter(frames))
    monkeypatch.setattr(audio_engine, "play_sound", lambda p, loop=False: None)
    monkeypatch.setattr(emotional_state, "get_last_emotion", lambda: "joy")
    wave = np.array([1.0, 1.0, 0.0, 0.0], dtype=np.float32)
    monkeypatch.setattr(aee.librosa, "load", lambda *a, **k: (wave, 4))

    out = list(aee.stream_avatar_audio(Path("x.wav"), fps=2))
    assert len(out) == 2
    open_pixels = out[0][-1].sum()
    closed_pixels = out[1][-1].sum()
    assert open_pixels > closed_pixels

