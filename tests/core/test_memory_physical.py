"""Tests for memory physical."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from core import memory_physical as mp

__version__ = "0.0.0"


class _Cv2Stub:
    @staticmethod
    def imwrite(path: str, frame: object) -> None:
        Path(path).write_text("frame")


class _LibrosaStub:
    class util:  # type: ignore[no-redef]
        @staticmethod
        def normalize(data):
            return data


class _SoundfileStub:
    def write(self, path, data, sr):
        Path(path).write_text("audio")


class _WhisperModel:
    def transcribe(self, path):
        return {"text": "ok"}


class _WhisperStub:
    @staticmethod
    def load_model(name):
        return _WhisperModel()


def test_store_text_event(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    event = mp.PhysicalEvent(modality="text", data="hello")
    meta_path = mp.store_physical_event(event)
    meta = json.loads(meta_path.read_text())
    assert meta["modality"] == "text"
    assert (tmp_path / meta["file"]).read_text() == "hello"


def test_store_audio_event(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(mp, "librosa", _LibrosaStub())
    monkeypatch.setitem(sys.modules, "soundfile", _SoundfileStub())
    monkeypatch.setattr(mp, "whisper", _WhisperStub())
    samples = np.array([0.1, -0.1])
    event = mp.PhysicalEvent(modality="audio", data=samples, sample_rate=44100)
    meta_path = mp.store_physical_event(event)
    meta = json.loads(meta_path.read_text())
    assert meta["modality"] == "audio"
    assert meta["transcription"] == "ok"
    assert (tmp_path / meta["file"]).read_text() == "audio"


def test_store_video_event(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(mp, "cv2", _Cv2Stub())
    event = mp.PhysicalEvent(modality="video", data="frame")
    meta_path = mp.store_physical_event(event)
    meta = json.loads(meta_path.read_text())
    assert meta["modality"] == "video"
    assert (tmp_path / meta["file"]).read_text() == "frame"


def test_unknown_modality(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    event = mp.PhysicalEvent(modality="unknown", data="x")
    with pytest.raises(ValueError):
        mp.store_physical_event(event)


def test_audio_requires_librosa(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(mp, "librosa", None)
    event = mp.PhysicalEvent(modality="audio", data="x", sample_rate=1)
    with pytest.raises(RuntimeError):
        mp.store_physical_event(event)


def test_audio_requires_sample_rate(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(mp, "librosa", _LibrosaStub())
    monkeypatch.setitem(sys.modules, "soundfile", _SoundfileStub())
    event = mp.PhysicalEvent(modality="audio", data=np.array([0.1]))
    with pytest.raises(ValueError):
        mp.store_physical_event(event)


def test_text_requires_string(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    with pytest.raises(ValueError):
        mp.store_physical_event(mp.PhysicalEvent(modality="text", data=123))


def test_video_requires_cv2(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(mp, "cv2", None)
    event = mp.PhysicalEvent(modality="video", data="frame")
    with pytest.raises(RuntimeError):
        mp.store_physical_event(event)
