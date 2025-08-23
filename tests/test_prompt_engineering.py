"""Tests for prompt engineering."""

from __future__ import annotations

from prompt_engineering import apply_style_preset


def test_ltx_preset_applied():
    prompt = "paint a sunset"
    result = apply_style_preset(prompt, "ltx")
    assert result == "Render with LTX flair: paint a sunset"


def test_pusa_preset_applied():
    prompt = "compose a melody"
    result = apply_style_preset(prompt, "pusa_v1")
    assert result == "Channeling PUSA V1 vibe: compose a melody"


def test_unknown_preset_returns_prompt():
    prompt = "draw a tree"
    result = apply_style_preset(prompt, "unknown")
    assert result == prompt
