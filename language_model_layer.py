from __future__ import annotations

"""Helpers for preparing language model insights for spoken summaries.

The insight system generates structured metrics describing how well different
prompt patterns perform. This module provides utilities that turn those
metrics into short, natural language phrases. The resulting text can then be
spoken by a text-to-speech backend or written to logs for debugging and
analysis.
"""

from typing import Dict


def convert_insights_to_spelling(insights: Dict[str, dict]) -> str:
    """Return a spoken summary of ``insights``.

    The mapping is expected to contain intent names as keys. Each value may
    provide a ``counts`` dictionary with ``total`` and ``success`` integers and
    an optional ``best_tone`` describing the most effective emotional delivery.
    Keys prefixed with an underscore are skipped so auxiliary metadata does not
    leak into the summary.

    When ``total`` is present the function calculates the success rate as a
    percentage and appends the recommended tone. If ``total`` is missing or set
    to zero a placeholder message notes that no data exists for that intent.

    Parameters
    ----------
    insights:
        Mapping of intent names to dictionaries containing insight statistics.

    Returns
    -------
    str
        A space separated summary where each intent is described by its success
        rate and recommended tone.

    Examples
    --------
    >>> convert_insights_to_spelling({
    ...     "greet": {"counts": {"total": 4, "success": 3}, "best_tone": "warm"}
    ... })
    'For pattern greet, success rate is 75 percent. Recommended tone is warm.'
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
