from __future__ import annotations

"""Simple finite state engine based on emotional cues."""

from typing import List

from INANNA_AI import emotion_analysis


class StateTransitionEngine:
    """Track ritual activation state."""

    STATES = ("dormant", "active", "ritual")

    def __init__(self) -> None:
        self._state = "dormant"
        self._history: List[str] = []

    def _detect_emotion(self, text: str) -> str:
        lowered = text.lower()
        for key in emotion_analysis.EMOTION_ARCHETYPES:
            if key in lowered:
                return key
        return "neutral"

    def _recent_ritual_cues(self) -> bool:
        return any("ritual" in e.lower() for e in self._history[-3:])

    def update_state(self, event: str) -> str:
        """Update and return current state based on ``event`` text."""
        self._history.append(event)
        if len(self._history) > 5:
            self._history.pop(0)
        emotion = self._detect_emotion(event)
        weight = emotion_analysis.emotion_weight(emotion)
        lowered = event.lower()
        if "ritual" in lowered or self._recent_ritual_cues():
            self._state = "ritual"
        elif "activate" in lowered or "start" in lowered or weight >= 0.5:
            self._state = "active"
        elif weight < 0.3:
            self._state = "dormant"
        return self._state

    def current_state(self) -> str:
        """Return the current state."""
        return self._state


__all__ = ["StateTransitionEngine"]
