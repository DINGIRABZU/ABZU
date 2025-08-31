from pathlib import Path

import numpy as np
import sys

from src.audio import mix_tracks
from core import memory_physical as mp

__version__ = "0.0.0"


class _LibrosaStub:
    class util:
        @staticmethod
        def normalize(data):
            return data


class _SoundfileStub:
    def write(self, path, data, sr):
        Path(path).write_text("mix")


def test_mix_then_store(tmp_path, monkeypatch):
    a = np.array([0.0, 1.0])
    b = np.array([1.0, 0.0])

    def fake_load(path, logger=None):
        return (a if "a" in str(path) else b), 44100

    monkeypatch.setattr(mix_tracks, "_load", fake_load)
    monkeypatch.setattr(mix_tracks.audio_ingestion, "extract_tempo", lambda d, s: 100.0)
    monkeypatch.setattr(mix_tracks.audio_ingestion, "extract_key", lambda d: "C")
    mix, sr, _ = mix_tracks.mix_audio([Path("a"), Path("b")])

    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(mp, "librosa", _LibrosaStub())
    monkeypatch.setitem(sys.modules, "soundfile", _SoundfileStub())
    event = mp.PhysicalEvent(modality="audio", data=mix, sample_rate=sr)
    meta_path = mp.store_physical_event(event)
    assert (tmp_path / meta_path.name).exists()
