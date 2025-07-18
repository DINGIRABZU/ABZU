import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import speaking_engine, utils as ai_utils


def test_stream_latency(tmp_path, monkeypatch):
    wave = np.zeros(int(44100), dtype=np.float32)
    out = tmp_path / "x.wav"
    ai_utils.save_wav(wave, str(out), sr=44100)

    monkeypatch.setattr(speaking_engine, "synthesize_speech", lambda *a, **k: str(out))
    monkeypatch.setattr(speaking_engine, "load_audio", lambda p, sr=None, mono=True: (wave, 44100))
    monkeypatch.setattr(speaking_engine, "convert_voice", lambda w, sr, timbre: w)

    engine = speaking_engine.SpeakingEngine()
    segments = list(engine.stream("hi", "neutral", segment_duration=0.2))

    assert segments
    assert all(len(seg[0]) <= int(44100 * 0.5) for seg in segments)
