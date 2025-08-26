from __future__ import annotations

import numpy as np
import pytest
from types import SimpleNamespace

from agents.bana.bio_adaptive_narrator import generate_story
from tests.agents.test_bana import synthetic_ecg


class DummyGenerator:
    def __init__(self) -> None:
        self.prompt: str | None = None

    def __call__(self, prompt: str, max_new_tokens: int, num_return_sequences: int):
        self.prompt = prompt
        return [{"generated_text": "Once upon a time."}]


def test_generate_story(monkeypatch, synthetic_ecg):
    """generate_story returns narrative text using biosignal input."""

    def fake_ecg(signal, sampling_rate, show):  # noqa: D401
        assert sampling_rate == 1000.0
        return {"heart_rate": np.array([80.0])}

    monkeypatch.setattr(
        "agents.bana.bio_adaptive_narrator.ecg", SimpleNamespace(ecg=fake_ecg)
    )
    generator = DummyGenerator()
    monkeypatch.setattr(
        "agents.bana.bio_adaptive_narrator.pipeline", lambda *a, **k: generator
    )
    logged: list[str] = []
    monkeypatch.setattr(
        "memory.narrative_engine.log_story", lambda text: logged.append(text)
    )

    story = generate_story(synthetic_ecg)

    assert story == "Once upon a time."
    assert "80.0 BPM" in generator.prompt
    assert logged == ["Once upon a time."]
