"""Helpers for preparing language model insights for spoken summaries.

The insight system generates structured metrics describing how well different
prompt patterns perform. This module provides utilities that turn those metrics
into short natural language phrases. The resulting text can then be spoken by a
text-to-speech backend or written to logs for debugging and analysis.

Each insight entry is mapped to a single sentence describing the success rate
and suggested delivery tone. Only lightweight, side‑effect free helpers live
here so the module can be reused by the CLI, the server or other tools without
pulling in heavy dependencies.  Missing fields are handled gracefully so callers
may pass partially filled mappings without defensive checks.
"""

from __future__ import annotations

from typing import Dict, Optional


def convert_insights_to_spelling(insights: Optional[Dict[str, dict]]) -> str:
    """Return a spoken summary of ``insights``.

    The mapping is expected to contain intent names as keys. Each value may
    provide a ``counts`` dictionary with ``total`` and ``success`` integers and
    an optional ``best_tone`` describing the most effective emotional delivery.
    Keys prefixed with an underscore are skipped so auxiliary metadata does not
    leak into the summary.

    When ``total`` is present the function calculates the success rate as a
    percentage and appends the recommended tone. If ``total`` is missing, not an
    integer or set to zero a placeholder message notes that no data exists for
    that intent.  The recommended tone falls back to ``"neutral"`` when the
    field is missing or empty.  ``success`` values greater than ``total`` and any
    negative numbers are clipped to keep the percentage within sensible bounds.

    Parameters
    ----------
    insights:
        Mapping of intent names to dictionaries containing insight statistics.
        ``None`` or an empty mapping returns an empty string.

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

    if not insights:
        return ""

    phrases = []
    for name, info in insights.items():
        if name.startswith("_"):
            continue
        counts = info.get("counts") or {}
        try:
            total = int(counts.get("total", 0))
            success = int(counts.get("success", 0))
        except (TypeError, ValueError):
            total, success = 0, 0
        total = max(total, 0)
        success = max(min(success, total), 0)
        best_tone = (info.get("best_tone") or "neutral").strip() or "neutral"
        if total > 0:
            rate = round(success / total * 100)
            phrases.append(
                f"For pattern {name}, success rate is {rate} percent. "
                f"Recommended tone is {best_tone}."
            )
        else:
            phrases.append(f"No data for pattern {name}.")

    return " ".join(phrases)


__all__ = ["convert_insights_to_spelling"]
