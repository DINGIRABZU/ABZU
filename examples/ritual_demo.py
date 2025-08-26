#!/usr/bin/env python3
"""Minimal emotion→music→insight demonstration.

1. Records an emotion via :mod:`emotional_state`.
2. Attempts to compose ritual music with :mod:`audio.play_ritual_music` and
   falls back to a bundled tone if the module is unavailable.
3. Logs the result to the spiral cortex memory.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # Optional dependency
    from audio.play_ritual_music import compose_ritual_music
except Exception:  # pragma: no cover - graceful fallback
    compose_ritual_music = None  # type: ignore

from emotional_state import set_last_emotion
from memory import spiral_cortex

ASSET_DIR = Path(__file__).resolve().parent / "assets"
TONE_FILE = ASSET_DIR / "ritual_tone.wav"


def play_audio(path: Path) -> None:
    """Play ``path`` using :mod:`simpleaudio` if available."""
    try:  # pragma: no cover - optional dependency
        import simpleaudio as sa

        wave_obj = sa.WaveObject.from_wave_file(str(path))
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as exc:  # pragma: no cover - optional dependency
        logging.warning("audio playback skipped: %s", exc)


def main() -> None:
    """Run the ritual demo."""
    emotion = "joy"

    # 1. Record the active emotion
    set_last_emotion(emotion)

    if compose_ritual_music:
        # 2a. Generate music tied to the emotion
        track = compose_ritual_music(emotion, ritual="\u2609")
        snippet = {"text": f"generated {emotion} ritual", "path": str(track.path)}
    else:
        # 2b. Fallback playback of bundled tone
        play_audio(TONE_FILE)
        track = None
        snippet = {"text": "played ritual tone"}

    # 3. Log an insight referencing the produced track or tone
    spiral_cortex.log_insight("ritual demo", [snippet], sentiment=0.5)

    if track:
        print(f"Ritual demo complete; audio at {track.path}")
    else:
        print("Ritual demo complete; audio backend unavailable")


if __name__ == "__main__":
    main()
