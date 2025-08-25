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
        self.samples: dict[str, Path] = {}
        self._model: Optional[object] = None

    def capture_sample(
        self,
        path: Path,
        seconds: float = 3.0,
        sr: int = 22_050,
        speaker: str = "user",
    ) -> Path:
        """Record ``seconds`` of audio from the microphone into ``path``.

        Parameters
        ----------
        path:
            Location to store the recorded WAV file.
        seconds:
            Duration of the recording.
        sr:
            Target sample rate.
        speaker:
            Identifier for the speaker profile.
        """

        if getattr(sd, "__stub__", False):
            raise RuntimeError("sounddevice library not installed")
        logger.info(
            "Recording voice sample for %.1f seconds (sr=%d) as '%s'",
            seconds,
            sr,
            speaker,
        )
        audio = sd.rec(int(seconds * sr), samplerate=sr, channels=1, dtype="float32")
        sd.wait()
        save_wav(np.asarray(audio).flatten(), str(path), sr=sr)
        self.samples[speaker] = path
        if self._model is not None and not getattr(emotivoice, "__stub__", False):
            self._model.register_voice(speaker, str(path))
        return path

    def synthesize(
        self,
        text: str,
        out_path: Path,
        speaker: str = "user",
        emotion: str = "neutral",
    ) -> Path:
        """Generate ``text`` with the cloned voice.

        Parameters
        ----------
        text:
            Text to be spoken.
        out_path:
            Destination WAV path.
        speaker:
            Speaker profile to use.
        emotion:
            Emotion hint for the synthesizer.
        """

        if getattr(emotivoice, "__stub__", False):
            raise RuntimeError("EmotiVoice library not installed")
        if speaker not in self.samples:
            raise RuntimeError(f"No voice sample captured for speaker '{speaker}'")
        if self._model is None:
            self._model = emotivoice.TTS()
            for name, samp in self.samples.items():
                self._model.register_voice(name, str(samp))
        self._model.tts_to_file(text, str(out_path), speaker=speaker, emotion=emotion)
        return out_path


__all__ = ["VoiceCloner"]
