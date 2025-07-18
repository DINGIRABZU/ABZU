from __future__ import annotations

import json
from pathlib import Path

"""Simple heuristics for classifying input text."""

INSTRUCTION_KEYWORDS = {
    "how to",
    "step",
    "instructions",
    "tutorial",
    "guide",
}

EMOTIONAL_KEYWORDS = {
    "feel",
    "emotion",
    "sad",
    "happy",
    "love",
    "hate",
}

PHILOSOPHY_KEYWORDS = {
    "meaning of life",
    "existence",
    "philosophy",
    "why are we",
    "purpose",
}

TECHNICAL_KEYWORDS = {
    "error",
    "exception",
    "traceback",
    "install",
    "import",
    "code",
}

_RITUAL_FILE = Path(__file__).resolve().parent / "ritual_profile.json"
try:
    _RITUAL_PROFILE: dict[str, dict[str, list[str]]] = json.loads(
        _RITUAL_FILE.read_text(encoding="utf-8")
    )
except Exception:  # pragma: no cover - missing file
    _RITUAL_PROFILE = {}


def ritual_action_sequence(condition: str, emotion: str) -> list[str]:
    """Return ritual actions for ``condition`` and ``emotion``."""
    info = _RITUAL_PROFILE.get(condition, {})
    return list(info.get(emotion, []))


def classify_task(text: str | dict) -> str:
    """Return a coarse category for ``text`` or data dict."""
    if isinstance(text, dict):
        if "ritual_condition" in text or "emotion_trigger" in text:
            return "ritual"
        lowered = str(text.get("text", "")).lower()
    else:
        lowered = str(text).lower()
    if any(k in lowered for k in INSTRUCTION_KEYWORDS):
        return "instructional"
    if any(k in lowered for k in EMOTIONAL_KEYWORDS):
        return "emotional"
    if any(k in lowered for k in PHILOSOPHY_KEYWORDS):
        return "philosophical"
    return "technical"


__all__ = ["classify_task", "ritual_action_sequence"]
