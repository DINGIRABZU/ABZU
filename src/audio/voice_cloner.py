from __future__ import annotations

"""Clone a user's voice using the optional EmotiVoice library."""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from core.utils.optional_deps import lazy_import
from INANNA_AI.utils import save_wav

sd = lazy_import("sounddevice")
emotivoice = lazy_import("emotivoice")
sf = lazy_import("soundfile")

logger = logging.getLogger(__name__)


class VoiceCloner:
    """Capture a short sample and synthesise cloned speech.

    The implementation relies on ``sounddevice`` for recording and
    ``EmotiVoice`` for speech synthesis. Both dependencies are optional. When
    they are not installed the class falls back to generating silence so the
    call succeeds, albeit with low quality.
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
            logger.warning("sounddevice library not installed, generating silence")
            audio = np.zeros(int(seconds * sr), dtype=np.float32)
        else:
            logger.info(
                "Recording voice sample for %.1f seconds (sr=%d) as '%s'",
                seconds,
                sr,
                speaker,
            )
            audio = sd.rec(
                int(seconds * sr), samplerate=sr, channels=1, dtype="float32"
            )
            sd.wait()
            audio = np.asarray(audio).flatten()
        save_wav(audio, str(path), sr=sr)
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
    ) -> Tuple[Path, float]:
        """Generate ``text`` with the cloned voice and estimate quality.

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

        if speaker not in self.samples:
            raise RuntimeError(f"No voice sample captured for speaker '{speaker}'")

        if getattr(emotivoice, "__stub__", False):
            logger.warning("EmotiVoice library not installed, generating silence")
            duration = max(0.1, 0.2 * len(text.split()))
            sr = 22_050
            audio = np.zeros(int(duration * sr), dtype=np.float32)
            save_wav(audio, str(out_path), sr=sr)
        else:
            if self._model is None:
                self._model = emotivoice.TTS()
                for name, samp in self.samples.items():
                    self._model.register_voice(name, str(samp))
            self._model.tts_to_file(
                text, str(out_path), speaker=speaker, emotion=emotion
            )

        mos = self._estimate_mos(out_path)
        return out_path, mos

    @staticmethod
    def _estimate_mos(path: Path) -> float:
        """Return a crude MOS quality estimate for ``path``.

        The metric is based on average signal amplitude and ranges from 1 to 5.
        When required dependencies are missing, a baseline score of ``1`` is
        returned.
        """

        if getattr(sf, "__stub__", False):
            return 1.0
        try:
            data, _ = sf.read(str(path), dtype="float32")
        except Exception:  # pragma: no cover - I/O errors
            return 1.0
        amp = float(np.mean(np.abs(data)))
        return float(np.clip(1.0 + 4.0 * amp, 1.0, 5.0))


__all__ = ["VoiceCloner"]
