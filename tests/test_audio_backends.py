"""Tests for audio backends when soundfile is absent."""

from __future__ import annotations

import sys
from pathlib import Path
import types

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Ensure optional dependency placeholders
sys.modules.setdefault("simpleaudio", types.ModuleType("simpleaudio"))

import audio.backends as backends
import audio.play_ritual_music as prm


def test_get_backend_simpleaudio(monkeypatch, caplog):
    """SimpleAudioBackend is selected when soundfile is missing."""
    monkeypatch.setattr(backends, "sf", None)
    monkeypatch.setattr(backends, "sa", object())

    with caplog.at_level("INFO"):
        backend = backends.get_backend()

    assert isinstance(backend, backends.SimpleAudioBackend)
    assert "Selected SimpleAudioBackend" in caplog.text


def test_get_backend_noop(monkeypatch, caplog):
    """NoOpBackend is selected when both soundfile and simpleaudio are missing."""
    monkeypatch.setattr(backends, "sf", None)
    monkeypatch.setattr(backends, "sa", None)

    with caplog.at_level("INFO"):
        backend = backends.get_backend()

    assert isinstance(backend, backends.NoOpBackend)
    assert "Selected NoOpBackend" in caplog.text
    assert "soundfile and simpleaudio libraries not installed" in caplog.text


def test_archetype_mix_logs_when_soundfile_missing(monkeypatch, caplog):
    """_get_archetype_mix logs when soundfile is unavailable."""
    monkeypatch.setattr(prm.backends, "sf", None)
    prm._get_archetype_mix.cache_clear()

    with caplog.at_level("INFO"):
        mix = prm._get_archetype_mix("nigredo")

    assert isinstance(mix, np.ndarray)
    assert mix.size > 0
    assert "soundfile not available" in caplog.text
