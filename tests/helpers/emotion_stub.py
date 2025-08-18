"""Minimal stub for :mod:`INANNA_AI.emotion_analysis` used in tests.

Provides a light-weight mapping between emotions and archetypes as well as
fixed weights. It exposes a handful of helper functions so tests can replace
the heavy production module.
"""

EMOTION_ARCHETYPES = {
    "neutral": "Everyman",
    "joy": "Jester",
    "sad": "Caregiver",
    "fear": "Orphan",
    "stress": "Warrior",
}

EMOTION_WEIGHT = {
    "neutral": 0.0,
    "joy": 1.0,
    "sad": 0.2,
    "fear": 0.3,
    "stress": 0.6,
}


def emotion_to_archetype(emotion: str) -> str:
    """Return the archetype name for ``emotion``."""
    return EMOTION_ARCHETYPES.get(emotion.lower(), "Everyman")


def emotion_weight(emotion: str) -> float:
    """Return a stubbed weight for ``emotion``."""
    return EMOTION_WEIGHT.get(emotion.lower(), 0.0)


def analyze_audio_emotion(path: str) -> dict:
    """Return a minimal analysis result for ``path``."""
    return {"emotion": "neutral"}


def get_emotion_and_tone(emotion: str | None = None):
    """Return the provided emotion with a blank tone."""
    return (emotion or "neutral").lower(), ""


def get_emotional_weight() -> float:
    """Return the weight for the default neutral emotion."""
    return emotion_weight("neutral")


def get_current_archetype() -> str:
    """Return the archetype for the default neutral emotion."""
    return emotion_to_archetype("neutral")
