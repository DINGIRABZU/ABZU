#!/usr/bin/env python3
"""Display the last recorded emotion with its spiral glyph."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import emotional_state

_GLYPHS = {
    "joy": "🌀😊",
    "sadness": "🌀😢",
    "anger": "🌀😠",
    "fear": "🌀😨",
    "neutral": "🌀",
}


def main() -> None:
    emotion = emotional_state.get_last_emotion() or "neutral"
    glyph = _GLYPHS.get(emotion, _GLYPHS["neutral"])
    print(f"{glyph} {emotion}")


if __name__ == "__main__":
    main()
