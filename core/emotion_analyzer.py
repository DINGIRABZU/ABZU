from __future__ import annotations

"""Mood tracking and emotion analysis utilities."""

from typing import Any, Dict

import emotional_state
from INANNA_AI import emotion_analysis

from .contracts import EmotionAnalyzerService


class EmotionAnalyzer(EmotionAnalyzerService):
    """Track recent emotions and expose analysis helpers.

    The analyzer maintains an exponential moving average of emotion weights and
    returns enriched metadata describing the currently dominant mood.
    """

    def __init__(self, mood_alpha: float = 0.2) -> None:
        self.mood_alpha = mood_alpha
        self.mood_state: Dict[str, float] = {
            e: 1.0 if e == "neutral" else 0.0 for e in emotion_analysis.EMOTION_WEIGHT
        }

    def update_mood(self, emotion: str) -> None:
        """Update the internal ``mood_state`` for ``emotion``."""
        for key in list(self.mood_state):
            target = 1.0 if key.lower() == emotion.lower() else 0.0
            self.mood_state[key] = (1 - self.mood_alpha) * self.mood_state.get(
                key, 0.0
            ) + self.mood_alpha * target

    def analyze(self, emotion: str) -> Dict[str, Any]:
        """Return enriched data for ``emotion`` and update ``mood_state``."""
        self.update_mood(emotion)
        dominant = max(self.mood_state, key=self.mood_state.get)
        emotional_state.set_last_emotion(dominant)
        emotional_state.set_resonance_level(self.mood_state[dominant])
        return {
            "emotion": dominant,
            "archetype": emotion_analysis.emotion_to_archetype(dominant),
            "weight": emotion_analysis.emotion_weight(dominant),
        }
