"""Tests for language model layer."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import language_model_layer as lml


def test_convert_insights_to_spelling():
    insights = {
        "greet": {"counts": {"total": 10, "success": 7}, "best_tone": "friendly"},
        "farewell": {"counts": {"total": 0, "success": 0}, "best_tone": ""},
    }
    expected = (
        "For pattern greet, success rate is 70 percent. "
        "Recommended tone is friendly. No data for pattern farewell."
    )
    result = lml.convert_insights_to_spelling(insights)
    assert result == expected


def test_convert_insights_to_spelling_defaults():
    """Missing data and tone fall back to safe defaults."""
    assert lml.convert_insights_to_spelling(None) == ""
    result = lml.convert_insights_to_spelling(
        {"ask": {"counts": {"total": 2, "success": 1}}}
    )
    assert (
        result
        == "For pattern ask, success rate is 50 percent. Recommended tone is neutral."
    )
