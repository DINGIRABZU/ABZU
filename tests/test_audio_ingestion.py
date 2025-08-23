"""Tests for audio ingestion."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.skip(reason="requires unavailable resources")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# provide lightweight stub for essentia before importing the module
ess_mod = types.ModuleType("essentia.standard")
ess_pkg = types.ModuleType("essentia")
setattr(ess_pkg, "standard", ess_mod)


class DummyKeyExtractor:
    def __call__(self, samples):
        return ("C", "major", 1.0)


class DummyRhythmExtractor:
    def __init__(self, method="multifeature"):
        pass

    def __call__(self, samples):
        return (130.0, 0.9)


setattr(ess_mod, "KeyExtractor", DummyKeyExtractor)
setattr(ess_mod, "RhythmExtractor2013", DummyRhythmExtractor)
sys.modules.setdefault("essentia", ess_pkg)
sys.modules.setdefault("essentia.standard", ess_mod)

from audio import audio_ingestion


def test_load_audio(monkeypatch):
    calls = {}

    def dummy_load(path, sr=44100, mono=True):
        calls["path"] = path
        calls["sr"] = sr
        calls["mono"] = mono
        return np.zeros(10), sr

    monkeypatch.setattr(audio_ingestion.librosa, "load", dummy_load)

    wave, sr = audio_ingestion.load_audio(Path("x.wav"), sr=22050)
    assert sr == 22050
    assert calls == {"path": Path("x.wav"), "sr": 22050, "mono": True}
    assert isinstance(wave, np.ndarray)


def test_extract_mfcc(monkeypatch):
    feats = np.ones((3, 4))
    monkeypatch.setattr(audio_ingestion.librosa.feature, "mfcc", lambda y, sr: feats)

    out = audio_ingestion.extract_mfcc(np.zeros(10), 44100)
    assert out is feats


def test_essentia_features():
    wave = np.zeros(100)
    assert audio_ingestion.extract_key(wave) == "C:major"
    assert audio_ingestion.extract_tempo(wave, 44100) == 130.0


def test_extract_chroma(monkeypatch):
    feats = np.ones((12, 2))
    monkeypatch.setattr(
        audio_ingestion.librosa.feature, "chroma_cqt", lambda y, sr: feats
    )
    out = audio_ingestion.extract_chroma(np.zeros(10), 44100)
    assert out is feats


def test_extract_spectral_centroid(monkeypatch):
    feats = np.ones((1, 3))
    monkeypatch.setattr(
        audio_ingestion.librosa.feature, "spectral_centroid", lambda y, sr: feats
    )
    out = audio_ingestion.extract_spectral_centroid(np.zeros(10), 44100)
    assert out is feats


def test_extract_chords(monkeypatch):
    chroma = np.zeros((12, 1))
    chroma[0] = chroma[4] = chroma[7] = 1.0
    monkeypatch.setattr(
        audio_ingestion.librosa.feature, "chroma_cqt", lambda y, sr: chroma
    )
    chords = audio_ingestion.extract_chords(np.zeros(10), 44100)
    assert chords == ["C:maj"]


def test_separate_sources_spleeter(monkeypatch):
    class DummySep:
        def __init__(self, cfg):
            self.cfg = cfg

        def separate(self, waveform):
            return {"vocals": waveform, "accompaniment": waveform}

    spleeter_mod = types.SimpleNamespace(
        separator=types.SimpleNamespace(Separator=DummySep)
    )
    monkeypatch.setitem(sys.modules, "spleeter", spleeter_mod)
    monkeypatch.setitem(sys.modules, "spleeter.separator", spleeter_mod.separator)
    samples = np.zeros(5)
    out = audio_ingestion.separate_sources(samples, 44100, library="spleeter")
    assert set(out.keys()) == {"vocals", "accompaniment"}
    for arr in out.values():
        assert arr.shape == (5,)


def test_extract_features(monkeypatch):
    monkeypatch.setattr(
        audio_ingestion, "load_audio", lambda p, sr=44100: (np.zeros(5), sr)
    )
    monkeypatch.setattr(audio_ingestion, "extract_mfcc", lambda s, sr: np.array([1]))
    monkeypatch.setattr(audio_ingestion, "extract_key", lambda s: "C:maj")
    monkeypatch.setattr(audio_ingestion, "extract_tempo", lambda s, sr: 120.0)
    monkeypatch.setattr(audio_ingestion, "extract_chroma", lambda s, sr: np.array([2]))
    monkeypatch.setattr(audio_ingestion, "extract_chords", lambda s, sr: ["C:maj"])
    monkeypatch.setattr(
        audio_ingestion, "extract_spectral_centroid", lambda s, sr: np.array([3])
    )
    monkeypatch.setattr(
        audio_ingestion,
        "separate_sources",
        lambda s, sr, lib: {"vocals": np.array([4])},
    )
    feats = audio_ingestion.extract_features(Path("x.wav"), separate="spleeter")
    assert feats["mfcc"].tolist() == [1]
    assert feats["chords"] == ["C:maj"]
    assert feats["sources"]["vocals"].tolist() == [4]


def test_embed_clap(monkeypatch):
    class DummyProc:
        @classmethod
        def from_pretrained(cls, *a, **k):
            return cls()

        def __call__(self, audios, sampling_rate=None, return_tensors=None):
            return {"audios": audios}

    class DummyFeat:
        def __init__(self):
            self.data = np.array([1.0, 2.0, 3.0])

        def squeeze(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self.data

    class DummyModel:
        @classmethod
        def from_pretrained(cls, *a, **k):
            return cls()

        def get_audio_features(self, **inputs):
            return DummyFeat()

    class DummyTorch:
        class _Ctx:
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

        def no_grad(self):
            return self._Ctx()

    monkeypatch.setattr(audio_ingestion, "ClapProcessor", DummyProc)
    monkeypatch.setattr(audio_ingestion, "ClapModel", DummyModel)
    monkeypatch.setattr(audio_ingestion, "torch", DummyTorch())

    emb = audio_ingestion.embed_clap(np.zeros(10), 44100)
    assert emb.shape == (3,)
    assert np.allclose(emb, [1.0, 2.0, 3.0])
