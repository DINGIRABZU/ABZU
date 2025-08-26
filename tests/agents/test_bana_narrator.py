from __future__ import annotations

import numpy as np
import pytest

from agents.bana.bio_adaptive_narrator import generate_story


class DummyGenerator:
    def __init__(self) -> None:
        self.prompt: str | None = None

    def __call__(self, prompt: str, max_new_tokens: int, num_return_sequences: int):
        self.prompt = prompt
        return [{"generated_text": "Once upon a time."}]


def test_generate_story(monkeypatch):
    """generate_story returns narrative text using biosignal input."""

    def fake_ecg(signal, sampling_rate, show):  # noqa: D401
        return {"heart_rate": np.array([80.0])}

    monkeypatch.setattr(
        "agents.bana.bio_adaptive_narrator.ecg.ecg", fake_ecg
    )
    generator = DummyGenerator()
    monkeypatch.setattr(
        "agents.bana.bio_adaptive_narrator.pipeline", lambda *a, **k: generator
    )

    story = generate_story([0.1, 0.2, 0.3])

    assert story == "Once upon a time."
    assert "80.0 BPM" in generator.prompt
