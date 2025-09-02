"""Tests for hex to glyphs smoke."""

from __future__ import annotations

import numpy as np

from SPIRAL_OS.qnl_engine import hex_to_song


def test_hex_input_to_musical_glyphs_smoke() -> None:
    phrases, wave = hex_to_song("00ff", duration_per_byte=0.01, sample_rate=100)
    glyphs = [p["phrase"].split(" + ")[0] for p in phrases]
    assert glyphs == ["❣⟁", "🕯✧"]
    assert isinstance(wave, np.ndarray)
