from __future__ import annotations

"""Lightweight context memory for recent user prompts."""

from collections import deque
from typing import Deque, List

_MAX_ENTRIES = 5
_CONTEXT: Deque[str] = deque(maxlen=_MAX_ENTRIES)


def add(text: str) -> None:
    """Add ``text`` to the context memory."""
    _CONTEXT.append(text)


def recent(n: int = 3) -> List[str]:
    """Return up to ``n`` most recent context entries."""
    if n <= 0:
        return []
    return list(_CONTEXT)[-n:]


__all__ = ["add", "recent"]
