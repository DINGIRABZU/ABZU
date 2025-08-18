"""Minimal stub for :mod:`INANNA_AI.emotion_analysis` used in tests."""

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

_current_emotion = "neutral"


def emotion_to_archetype(emotion: str) -> str:
    """Return archetype name for ``emotion``."""
    return EMOTION_ARCHETYPES.get(emotion.lower(), "Everyman")


def emotion_weight(emotion: str) -> float:
    """Return a stubbed weight for ``emotion``."""
    return EMOTION_WEIGHT.get(emotion.lower(), 0.0)


def get_emotion_and_tone(emotion: str | None = None):
    """Return the emotion (updating current) with a blank tone."""
    global _current_emotion
    _current_emotion = (emotion or _current_emotion).lower()
    return _current_emotion, ""


def get_emotional_weight() -> float:
    """Return weight for the current emotion."""
    return emotion_weight(_current_emotion)


def get_current_archetype() -> str:
    """Return archetype for the current emotion."""
    return emotion_to_archetype(_current_emotion)


def analyze_audio_emotion(path: str) -> dict:
    """Return a minimal emotion analysis result for ``path``."""
    return {"emotion": _current_emotion}
