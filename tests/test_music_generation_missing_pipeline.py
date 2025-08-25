"""Tests for missing transformers pipeline."""

from __future__ import annotations

import pytest

pytest.importorskip("omegaconf")

import music_generation as mg


def test_missing_hf_pipeline_raises(monkeypatch):
    monkeypatch.setattr(mg, "hf_pipeline", None)
    gen = mg.MusicGenerator()
    with pytest.raises(ImportError):
        gen.process("beat")
