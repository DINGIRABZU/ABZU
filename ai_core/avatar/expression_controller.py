from __future__ import annotations

"""Generate rudimentary facial landmarks based on dialogue cues."""

from typing import Dict, List, Tuple

Landmarks = Dict[str, List[Tuple[int, int]]]

# Predefined landmark templates.  Coordinates assume a 100x100 canvas for
# simplicity; callers are expected to scale as required.
_NEUTRAL: Landmarks = {
    "eyes": [(30, 40), (70, 40)],
    "mouth": [(40, 70), (50, 75), (60, 70)],
}
_HAPPY: Landmarks = {
    "eyes": [(30, 35), (70, 35)],  # slightly raised eyebrows
    "mouth": [(40, 65), (50, 80), (60, 65)],
}
_SAD: Landmarks = {
    "eyes": [(30, 45), (70, 45)],
    "mouth": [(40, 75), (50, 60), (60, 75)],
}


def generate_landmarks(dialogue: str) -> Landmarks:
    """Return facial landmarks inferred from ``dialogue``.

    The heuristic implementation looks for simple emotional cues.  If no cues
    are detected the neutral template is returned.  The function is intentionally
    lightweight and deterministic to keep unit tests fast and predictable.
    """

    cue = dialogue.lower()
    if any(word in cue for word in {"smile", "happy", "joy"}):
        return _HAPPY
    if any(word in cue for word in {"sad", "frown", "cry"}):
        return _SAD
    return _NEUTRAL


__all__ = ["generate_landmarks", "Landmarks"]
