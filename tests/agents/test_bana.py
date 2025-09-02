"""Tests for bana."""

from __future__ import annotations

import numpy as np
import pytest
from types import SimpleNamespace

from agents.bana.bio_adaptive_narrator import generate_story


@pytest.fixture
def synthetic_ecg() -> np.ndarray:
    """Return a 1-second synthetic ECG-like signal."""
    t = np.linspace(0, 1, 1000, endpoint=False)
    return np.sin(2 * np.pi * 1.0 * t)


def test_generate_story_with_valid_signal(monkeypatch, synthetic_ecg):
    """Story generation works with valid data and logs output."""

    def fake_ecg(signal, sampling_rate, show):  # noqa: D401
        assert sampling_rate == 1000.0
        return {"heart_rate": np.array([72.0])}

    monkeypatch.setattr(
        "agents.bana.bio_adaptive_narrator.ecg", SimpleNamespace(ecg=fake_ecg)
    )

    class DummyGenerator:
        def __call__(self, prompt, max_new_tokens, num_return_sequences):
            return [{"generated_text": "Narrative"}]

    monkeypatch.setattr(
        "agents.bana.bio_adaptive_narrator.pipeline", lambda *a, **k: DummyGenerator()
    )
    logged: list[str] = []
    monkeypatch.setattr(
        "memory.narrative_engine.log_story", lambda text: logged.append(text)
    )

    story = generate_story(synthetic_ecg)
    assert story == "Narrative"
    assert logged == ["Narrative"]


def test_invalid_sampling_rate(synthetic_ecg):
    """Non-positive sampling rates raise an error."""

    with pytest.raises(ValueError):
        generate_story(synthetic_ecg, sampling_rate=0)


def test_short_signal(monkeypatch):
    """Signals shorter than one second are rejected."""

    short_signal = np.zeros(100)
    with pytest.raises(ValueError):
        generate_story(short_signal, sampling_rate=1000.0)
