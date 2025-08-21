from __future__ import annotations

"""Map sigils to actions or emotion modifiers."""

from typing import Dict, List

SIGIL_MAP: Dict[str, str] = {
    "🜂": "anger",
    "🜁": "calm",
    "🜄": "sadness",
    "🜃": "joy",
}


def interpret_sigils(text: str) -> List[str]:
    """Return triggers found in ``text`` based on :data:`SIGIL_MAP`."""
    triggers: List[str] = []
    for char in text:
        trig = SIGIL_MAP.get(char)
        if trig:
            triggers.append(trig)
    return triggers


__all__ = ["SIGIL_MAP", "interpret_sigils"]
