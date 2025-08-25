"""Tests for voice cloning CLI and API using stubbed dependencies."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Stub optional dependencies before importing modules under test


sd = types.SimpleNamespace(__stub__=False)


def _rec(n, samplerate, channels, dtype):  # pragma: no cover - trivial
    return np.zeros((n, channels), dtype=np.float32)


sd.rec = _rec
sd.wait = lambda: None
sys.modules.setdefault("sounddevice", sd)


ev = types.SimpleNamespace(__stub__=False)


class _DummyTTS:  # pragma: no cover - simple behaviour
    def __init__(self) -> None:
        self.voices = {}

    def register_voice(self, name: str, path: str) -> None:
        self.voices[name] = path

    def tts_to_file(self, text: str, out: str, speaker: str, emotion: str) -> None:
        Path(out).write_text(f"{speaker}:{emotion}:{text}")


ev.TTS = _DummyTTS
sys.modules.setdefault("emotivoice", ev)


sf = types.SimpleNamespace(write=lambda p, d, sr, subtype=None: Path(p).write_bytes(b""))
sys.modules.setdefault("soundfile", sf)


from src.cli.voice_clone import main as cli_main
from src.api.server import app


def test_cli_capture_and_synthesize(tmp_path):
    sample = tmp_path / "sample.wav"
    out = tmp_path / "out.wav"
    cli_main([
        "capture",
        str(sample),
        "--speaker",
        "alice",
        "--seconds",
        "0.1",
        "--sr",
        "8000",
    ])
    cli_main(
        [
            "synthesize",
            "hi",
            str(out),
            "--sample",
            str(sample),
            "--speaker",
            "alice",
            "--emotion",
            "joy",
        ]
    )
    assert out.exists()


def test_api_capture_and_synthesize(tmp_path):
    client = TestClient(app)
    sample = tmp_path / "sample.wav"
    out = tmp_path / "out.wav"
    r = client.post(
        "/voice/capture",
        json={"path": str(sample), "speaker": "bob", "seconds": 0.1, "sr": 8000},
    )
    assert r.status_code == 200 and r.json()["speaker"] == "bob"
    r = client.post(
        "/voice/synthesize",
        json={"text": "ok", "speaker": "bob", "emotion": "sad", "out": str(out)},
    )
    assert r.status_code == 200
    assert out.exists()


