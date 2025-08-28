from __future__ import annotations

"""Helper for voice cloning within the console interface."""

import logging
from pathlib import Path

from audio import voice_cloner
from INANNA_AI import speaking_engine

logger = logging.getLogger(__name__)


def clone_voice(sample_text: str) -> voice_cloner.VoiceCloner | None:
    """Capture a voice sample and synthesize ``sample_text``.

    Returns the ``VoiceCloner`` instance if cloning succeeds, otherwise ``None``.
    """
    try:
        vc = voice_cloner.VoiceCloner()
        sample_path = Path("data/voice_sample.wav")
        out_path = Path("data/voice_clone.wav")
        vc.capture_sample(sample_path)
        vc.synthesize(sample_text or "Voice clone ready.", out_path)
        speaking_engine.play_wav(str(out_path))
        print("Cloned voice registered for future replies.")
        return vc
    except Exception as exc:
        logger.error("Voice cloning unavailable: %s", exc)
        return None


__all__ = ["clone_voice"]
