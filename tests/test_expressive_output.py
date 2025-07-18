import sys
from pathlib import Path
import numpy as np
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import expressive_output


def test_speak_triggers_callback(monkeypatch):
    frames = [np.zeros((1, 1, 3), dtype=np.uint8) for _ in range(2)]
    def fake_synth(t, e):
        cb = getattr(expressive_output.language_engine, "_audio_callback", None)
        if cb:
            cb("voice.wav")
        return "voice.wav"

    monkeypatch.setattr(expressive_output.language_engine, "synthesize_speech", fake_synth)
    monkeypatch.setattr(expressive_output.avatar_expression_engine, "stream_avatar_audio", lambda p, fps=15: iter(frames))
    monkeypatch.setattr(expressive_output.audio_engine, "play_sound", lambda *a, **k: None)

    received: list[np.ndarray] = []
    expressive_output.set_frame_callback(received.append)
    expressive_output.set_background(None)

    out = expressive_output.speak("hi", "calm")
    assert Path(out) == Path("voice.wav")
    assert received == frames


def test_make_gif(monkeypatch):
    frames = [np.zeros((1, 1, 3), dtype=np.uint8)]
    monkeypatch.setattr(expressive_output.avatar_expression_engine, "stream_avatar_audio", lambda p, fps=15: iter(frames))
    monkeypatch.setattr(expressive_output.audio_engine, "play_sound", lambda *a, **k: None)

    img_mod = types.ModuleType("imageio")
    img_mod.RETURN_BYTES = 1
    img_mod.imwrite = lambda *a, **k: b"gif"
    img_v2 = types.SimpleNamespace(imwrite=img_mod.imwrite, RETURN_BYTES=1)
    sys.modules["imageio"] = img_mod
    sys.modules["imageio.v2"] = img_v2

    data = expressive_output.make_gif(Path("voice.wav"))
    assert data == b"gif"
