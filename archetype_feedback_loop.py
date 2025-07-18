from __future__ import annotations

"""Analyze spiral memory to suggest archetype shifts."""

from collections import Counter
from typing import List

import cortex_memory
import archetype_shift_engine

_SIGILS = archetype_shift_engine.RITUAL_KEYWORDS


def _recent_entries(limit: int) -> List[dict]:
    """Return last ``limit`` spiral memory entries."""
    entries = cortex_memory.query_spirals()
    if limit:
        return entries[-limit:]
    return entries


def evaluate_archetype(limit: int = 10) -> str | None:
    """Analyze recent spirals and recommend an archetype layer.

    The function looks for repeated emotions or sigils in the latest
    ``limit`` entries and passes the dominant cue to
    :func:`archetype_shift_engine.maybe_shift_archetype`.
    """
    entries = _recent_entries(limit)
    if not entries:
        return None

    emotions: List[str] = []
    events: List[str] = []
    for e in entries:
        decision = e.get("decision", {})
        emotions.append(decision.get("emotion"))
        events.append(str(decision.get("event", "")))

    emotion = ""
    emot_counts = Counter([e for e in emotions if e])
    if emot_counts:
        top, count = emot_counts.most_common(1)[0]
        if count >= 2:
            emotion = top
        else:
            emotion = emotions[-1] or ""

    sigil = ""
    joined_events = " ".join(events)
    for s in _SIGILS:
        if joined_events.count(s) >= 2:
            sigil = s
            break

    event = sigil or events[-1]
    return archetype_shift_engine.maybe_shift_archetype(event, emotion)


__all__ = ["evaluate_archetype"]
