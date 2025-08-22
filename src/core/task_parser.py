from __future__ import annotations

"""Simple text command parser returning structured intents."""

from typing import Dict, List


def parse(text: str) -> List[Dict[str, str]]:
    """Return intents detected in ``text``.

    Currently recognises the phrases "appear to me" and
    "initiate sacred communion".
    """
    lower = text.lower()
    intents: List[Dict[str, str]] = []
    if "appear to me" in lower:
        intents.append({"intent": "appear", "action": "show_avatar"})
    if "initiate sacred communion" in lower:
        intents.append({"intent": "communion", "action": "start_call"})
    return intents


__all__ = ["parse"]
