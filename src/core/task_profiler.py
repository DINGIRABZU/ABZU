"""Task profiling helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

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

_RITUAL_FILE = Path(__file__).resolve().parents[1] / "ritual_profile.json"


class TaskProfiler:
    """Classify text inputs and map ritual action sequences."""

    def __init__(
        self, *, ritual_profile: Dict[str, Dict[str, List[str]]] | None = None
    ) -> None:
        if ritual_profile is not None:
            self._ritual_profile = ritual_profile
        else:
            try:
                self._ritual_profile = json.loads(
                    _RITUAL_FILE.read_text(encoding="utf-8")
                )
            except Exception:  # pragma: no cover - missing file
                self._ritual_profile = {}

    def classify(self, text: str | Dict[str, Any]) -> str:
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

    def ritual_action_sequence(self, condition: str, emotion: str) -> List[str]:
        """Return ritual actions for ``condition`` and ``emotion``."""
        info = self._ritual_profile.get(condition, {})
        return list(info.get(emotion, []))


__all__ = ["TaskProfiler"]
