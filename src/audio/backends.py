from __future__ import annotations

"""Audio playback backends."""

from pathlib import Path
from threading import Thread
import logging
import numpy as np

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import simpleaudio as sa
except Exception:  # pragma: no cover - optional dependency
    sa = None  # type: ignore

from core import expressive_output

logger = logging.getLogger(__name__)


def _write_wav(path: Path, data: np.ndarray, sample_rate: int = 44100) -> None:
    """Write ``data`` to ``path`` as a mono WAV using the standard library."""
    path.parent.mkdir(parents=True, exist_ok=True)
    import wave

    clipped = np.clip(data, -1.0, 1.0)
    pcm = (clipped * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


class SoundfileBackend:
    """Backend that uses ``soundfile`` for writing and playback."""

    def play(self, path: Path, wave: np.ndarray, sample_rate: int = 44100) -> None:
        assert sf is not None
        sf.write(path, wave, sample_rate)
        logger.info("Playback using soundfile backend")
        Thread(
            target=expressive_output.play_audio,
            args=(path,),
            daemon=True,
        ).start()


class SimpleAudioBackend:
    """Backend that plays audio via ``simpleaudio``."""

    def play(self, path: Path, wave: np.ndarray, sample_rate: int = 44100) -> None:
        assert sa is not None
        _write_wav(path, wave, sample_rate)
        logger.info("Playback using simpleaudio backend")
        pcm = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
        Thread(
            target=lambda: sa.play_buffer(pcm, 1, 2, sample_rate).wait_done(),
            daemon=True,
        ).start()


class NoOpBackend:
    """Backend used when no audio library is available."""

    def play(self, path: Path, wave: np.ndarray, sample_rate: int = 44100) -> None:
        _write_wav(path, wave, sample_rate)
        logger.info("Audio playback disabled; WAV available at %s", path)


def get_backend():
    """Return an appropriate playback backend."""
    if sf is not None:
        logger.info("Selected SoundfileBackend")
        return SoundfileBackend()
    if sa is not None:
        logger.warning("soundfile library not installed; using simpleaudio backend")
        logger.info("Selected SimpleAudioBackend")
        return SimpleAudioBackend()
    logger.warning(
        "soundfile and simpleaudio libraries not installed; audio playback disabled"
    )
    return NoOpBackend()
