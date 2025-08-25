#!/usr/bin/env python3
"""Demonstration script for emotion setting, music playback, and insight logging.

The script performs three actions:

1. Sets the current emotion via :mod:`emotional_state`.
2. Plays a sample tone bundled under ``examples/assets``.
3. Logs a dummy insight to the spiral cortex memory.
"""
from __future__ import annotations

from pathlib import Path
import logging

from emotional_state import set_last_emotion
from memory import spiral_cortex

ASSET_DIR = Path(__file__).resolve().parent / "assets"
TONE_FILE = ASSET_DIR / "ritual_tone.wav"


def play_audio(path: Path) -> None:
    """Play ``path`` using :mod:`simpleaudio` if available."""
    try:
        import simpleaudio as sa  # type: ignore

        wave_obj = sa.WaveObject.from_wave_file(str(path))
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as exc:  # pragma: no cover - optional dependency
        logging.warning("audio playback skipped: %s", exc)


def main() -> None:
    """Run the ritual demo."""
    # 1. Set the active emotion
    set_last_emotion("joy")

    # 2. Play the ritual tone
    play_audio(TONE_FILE)

    # 3. Log an insight
    spiral_cortex.log_insight(
        "ritual demo",
        [{"text": "played ritual tone"}],
        sentiment=0.5,
    )

    print("Ritual demo complete.")


if __name__ == "__main__":
    main()
