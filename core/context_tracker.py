from __future__ import annotations

"""Simple runtime context flags."""

from dataclasses import dataclass


@dataclass
class ContextTracker:
    """State flags describing the current multimodal session."""

    in_call: bool = False
    avatar_loaded: bool = False


state = ContextTracker()

__all__ = ["state", "ContextTracker"]
