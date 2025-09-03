"""Tests for ritual invocation integration with music generation."""

from __future__ import annotations

from pathlib import Path

import music_generation as mg
import invocation_engine as ie


def test_invocation_triggers_generation(monkeypatch):
    ie.clear_registry()
    temp = Path("generated.wav")

    def fake_generate(prompt, *, emotion=None, **_):
        assert prompt == "\u266a"  # eighth note symbol
        assert emotion == "joy"
        return temp

    monkeypatch.setattr(mg, "generate_from_text", fake_generate)
    mg.register_music_invocation("\u266a", emotion="joy")

    result = ie.invoke("\u266a [joy]")
    assert result == [temp]
