from __future__ import annotations

"""Utilities for generating text from insight metrics."""

from typing import Dict


def convert_insights_to_spelling(insights: Dict[str, dict]) -> str:
    """Return spoken phrases summarizing ``insights``.

    Parameters
    ----------
    insights:
        Mapping of intent names to insight information.

    Returns
    -------
    str
        Human readable summary suitable for text-to-speech.
    """

    phrases = []
    for name, info in insights.items():
        if name.startswith("_"):
            continue
        counts = info.get("counts", {})
        total = counts.get("total", 0)
        success = counts.get("success", 0)
        best_tone = info.get("best_tone") or "neutral"
        if total:
            rate = round(success / total * 100)
            phrases.append(
                f"For pattern {name}, success rate is {rate} percent. "
                f"Recommended tone is {best_tone}."
            )
        else:
            phrases.append(f"No data for pattern {name}.")

    return " ".join(phrases)


__all__ = ["convert_insights_to_spelling"]
