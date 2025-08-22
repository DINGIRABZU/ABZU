from __future__ import annotations

"""Clone a user's voice using the optional EmotiVoice library."""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from core.utils.optional_deps import lazy_import
from INANNA_AI.utils import save_wav

sd = lazy_import("sounddevice")
emotivoice = lazy_import("emotivoice")

logger = logging.getLogger(__name__)


class VoiceCloner:
    """Capture a short sample and synthesise cloned speech.

    The implementation relies on ``sounddevice`` for recording and
    ``EmotiVoice`` for speech synthesis.  Both dependencies are optional and
    a :class:`RuntimeError` is raised when they are unavailable.
    """

    def __init__(self) -> None:
        self.sample: Optional[Path] = None
        self._model: Optional[object] = None

    def capture_sample(
        self, path: Path, seconds: float = 3.0, sr: int = 22_050
    ) -> Path:
        """Record ``seconds`` of audio from the microphone into ``path``."""

        if getattr(sd, "__stub__", False):
            raise RuntimeError("sounddevice library not installed")
        logger.info("Recording voice sample for %.1f seconds", seconds)
        audio = sd.rec(int(seconds * sr), samplerate=sr, channels=1, dtype="float32")
        sd.wait()
        save_wav(np.asarray(audio).flatten(), str(path), sr=sr)
        self.sample = path
        return path

    def synthesize(
        self, text: str, out_path: Path, emotion: str = "neutral"
    ) -> Path:
        """Generate ``text`` with the cloned voice."""

        if getattr(emotivoice, "__stub__", False):
            raise RuntimeError("EmotiVoice library not installed")
        if self.sample is None:
            raise RuntimeError("No voice sample captured")
        if self._model is None:
            self._model = emotivoice.TTS()
            self._model.register_voice("user", str(self.sample))
        self._model.tts_to_file(text, str(out_path), speaker="user", emotion=emotion)
        return out_path


__all__ = ["VoiceCloner"]

