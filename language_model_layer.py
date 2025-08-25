from __future__ import annotations

"""Language model helpers for converting insight metrics to speech-ready text.

The functions in this module transform structured insight data produced by
other components into short human readable statements. These statements can be
fed directly into a text-to-speech engine or logged for later analysis.
"""

from typing import Dict


def convert_insights_to_spelling(insights: Dict[str, dict]) -> str:
    """Return spoken phrases summarizing ``insights``.

    Parameters
    ----------
    insights:
        Mapping of intent names to dictionaries containing insight statistics.
        Each value may include a ``counts`` mapping with ``total`` and
        ``success`` integers and an optional ``best_tone`` string describing the
        most effective emotional tone.

    Returns
    -------
    str
        A space separated summary where each intent is described by its success
        rate and recommended tone. Keys starting with an underscore are
        ignored. If an intent has no ``total`` count, the summary notes that no
        data is available.

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
