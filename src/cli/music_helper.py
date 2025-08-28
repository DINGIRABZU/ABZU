from __future__ import annotations

"""Utility functions for handling music generation commands."""

import logging
from pathlib import Path

from INANNA_AI import speaking_engine
from tools import session_logger

logger = logging.getLogger(__name__)


def play_music(orch, prompt: str) -> None:
    """Generate and play music for ``prompt`` using ``orch``."""
    if not prompt:
        print("Usage: /music <prompt>")
        return
    try:
        result = orch.route(
            prompt,
            {},
            text_modality=False,
            voice_modality=False,
            music_modality=True,
        )
        music_path = result.get("music_path")
        if not music_path:
            print("No music generated.")
            return
        session_logger.log_audio(Path(music_path))
        try:
            speaking_engine.play_wav(music_path)
        except Exception:  # pragma: no cover - playback may fail
            logger.exception("music playback failed")
        print(f"Music saved to {music_path}")
    except Exception:  # pragma: no cover - generation may fail
        logger.exception("music generation failed")


__all__ = ["play_music"]
