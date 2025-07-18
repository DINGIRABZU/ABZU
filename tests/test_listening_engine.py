import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import listening_engine


def _sine(freq: float, amp: float, sr: int, duration: float = 0.5) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return amp * np.sin(2 * np.pi * freq * t)


def _mock_stream(monkeypatch, waves):
    """Patch sounddevice.InputStream to feed ``waves``."""
    class DummyStream:
        def __init__(self, samplerate=None, channels=1, blocksize=None, callback=None):
            self.callback = callback
        def start(self):
            for w in waves:
                self.callback(w.reshape(-1, 1), len(w), None, None)
        def stop(self):
            pass
        def close(self):
            pass
    dummy_sd = type("sd", (), {"InputStream": DummyStream})
    monkeypatch.setattr(listening_engine, "sd", dummy_sd)


def test_stream_chunks(monkeypatch):
    sr = 44100
    waves = [
        _sine(200, 0.3, sr),
        _sine(440, 0.6, sr),
        _sine(110, 0.05, sr),
    ]
    _mock_stream(monkeypatch, waves)
    engine = listening_engine.ListeningEngine(sr=sr, chunk_duration=0.5)

    results = list(engine.stream_chunks(duration=1.5))

    assert len(results) == 3
    expected = [listening_engine._extract_features(w, sr) for w in waves]
    for (wave, state), exp_wave, exp_state in zip(results, waves, expected):
        assert np.allclose(wave, exp_wave)
        assert state == exp_state


def test_record(monkeypatch, tmp_path):
    sr = 44100
    waves = [
        _sine(200, 0.3, sr),
        _sine(440, 0.6, sr),
        _sine(110, 0.05, sr),
    ]
    _mock_stream(monkeypatch, waves)

    saved = {}
    def dummy_save(wave, path, sr=44100):
        saved["wave"] = wave
        saved["path"] = path
        saved["sr"] = sr
        Path(path).write_bytes(b"dummy")
    monkeypatch.setattr(listening_engine.utils, "save_wav", dummy_save)

    engine = listening_engine.ListeningEngine(sr=sr, chunk_duration=0.5)
    path, state = engine.record(duration=1.5)

    assert Path(path).exists()
    assert saved["sr"] == sr
    assert len(saved["wave"]) == sr * 3 // 2
    assert state == listening_engine._extract_features(waves[-1], sr)


def test_stream_states(monkeypatch):
    """Engine should classify silence, speech and noise chunks."""
    sr = 44100
    waves = [
        np.zeros(int(sr * 0.5), dtype=np.float32),
        _sine(180, 0.4, sr),
        _sine(500, 0.4, sr),
    ]
    _mock_stream(monkeypatch, waves)
    engine = listening_engine.ListeningEngine(sr=sr, chunk_duration=0.5)

    states = [state for _, state in engine.stream_chunks(duration=1.5)]
    expected = [listening_engine._extract_features(w, sr) for w in waves]

    assert states == expected
    assert states[0]["silence_meaning"] == "Brief pause"
