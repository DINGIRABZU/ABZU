from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from core import video_engine
from audio import voice_aura


def test_audio_driven_lip_sync(monkeypatch, tmp_path):
    wave = np.linspace(0, 1, 30, dtype=np.float32)
    fake_librosa = types.SimpleNamespace(load=lambda *a, **k: (wave, 30))

    class DummyPred:
        def synthesize(self, frame, seg):
            out = frame.copy()
            out[0, 0, 0] = seg.sum()
            return out

    monkeypatch.setattr(video_engine, "librosa", fake_librosa)
    monkeypatch.setattr(video_engine, "Wav2LipPredictor", DummyPred)
    monkeypatch.setattr(video_engine, "mp", None)

    gen = video_engine.generate_avatar_stream(lip_sync_audio=tmp_path / "a.wav")
    frame1 = next(gen)
    frame2 = next(gen)
    assert frame1[0, 0, 0] != frame2[0, 0, 0]


def test_voice_aura_updates(monkeypatch, tmp_path):
    inp = tmp_path / "in.wav"
    inp.write_bytes(b"data")
    out = tmp_path / "out.wav"

    class DummyTmp:
        def __init__(self, path: Path) -> None:
            self.name = str(path)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(
        voice_aura,
        "tempfile",
        types.SimpleNamespace(NamedTemporaryFile=lambda **k: DummyTmp(out)),
    )
    monkeypatch.setattr(voice_aura, "sox_available", lambda: True)
    called = {}

    def fake_run(cmd, check):
        Path(cmd[2]).write_bytes(b"out")
        called["reverb"] = cmd[4]
        called["delay"] = cmd[6]

    monkeypatch.setattr(voice_aura.subprocess, "run", fake_run)
    monkeypatch.setattr(
        voice_aura,
        "sf",
        types.SimpleNamespace(
            read=lambda p, dtype="float32": (np.zeros(1, dtype=np.float32), 8000),
            write=lambda p, d, sr: None,
        ),
    )
    monkeypatch.setattr(voice_aura.emotional_state, "get_last_emotion", lambda: "joy")

    result = voice_aura.apply_voice_aura(inp)
    assert called["reverb"] == str(voice_aura.EFFECT_PRESETS["joy"]["reverb"])
    assert result.exists()
