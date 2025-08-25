"""Tests for graceful backend fallbacks."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("omegaconf")

import music_llm_interface as mli
import seven_dimensional_music as sdm


def test_analyze_midi_requires_pretty_midi(monkeypatch):
    monkeypatch.setattr(mli, "load_backend", lambda name: None)
    with pytest.raises(RuntimeError, match="pretty_midi"):
        mli._analyze_midi(Path("dummy.mid"))


def test_generate_quantum_music_requires_soundfile(monkeypatch, tmp_path):
    monkeypatch.setattr(sdm, "load_backend", lambda name: None)
    monkeypatch.setattr(sdm, "quantum_embed", lambda text: np.zeros(1, dtype=float))
    monkeypatch.setattr(sdm, "embedding_to_params", lambda emb: (0.0, 1.0, 1.0))
    with pytest.raises(RuntimeError, match="soundfile"):
        sdm.generate_quantum_music("ctx", "joy", output_dir=tmp_path)
