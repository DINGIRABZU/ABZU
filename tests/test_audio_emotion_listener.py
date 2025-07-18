import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import audio_emotion_listener
import emotional_state


def _sine(freq: float, amp: float, sr: int, duration: float = 0.5) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return amp * np.sin(2 * np.pi * freq * t)


def test_detect_emotion():
    sr = 44100
    wave = _sine(220, 0.3, sr)
    info = audio_emotion_listener.detect_emotion(wave, sr)
    assert "emotion" in info
    assert "pitch" in info
    assert "tempo" in info


def test_listen_for_emotion_updates_state(monkeypatch, mock_emotion_state):
    sr = 44100
    wave = _sine(440, 0.6, sr, 1.0)

    class DummySD:
        def rec(self, n, samplerate=sr, channels=1, dtype="float32"):
            return wave.reshape(-1, 1)

        def wait(self):
            pass

    monkeypatch.setattr(audio_emotion_listener, "sd", DummySD())

    info = audio_emotion_listener.listen_for_emotion(1.0, sr=sr)
    assert emotional_state.get_last_emotion() == info["emotion"]
    assert isinstance(info["emotion"], str)
