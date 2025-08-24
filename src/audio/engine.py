"""Simple playback engine for ritual loops and voice audio."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from threading import Event, Thread
from typing import Any

import numpy as np

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore
from audio.dsp_engine import (
    compress,
    nsynth_interpolate,
    pitch_shift,
    rave_decode,
    rave_encode,
    rave_morph,
    time_stretch,
)
from MUSIC_FOUNDATION.layer_generators import generate_tone

try:  # pragma: no cover - optional dependency
    from audio.segment import AudioSegment, NpAudioSegment
except Exception:  # pragma: no cover - optional dependency
    AudioSegment = None  # type: ignore
    NpAudioSegment = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from pydub.playback import _play_with_simpleaudio
except Exception:  # pragma: no cover - optional dependency
    _play_with_simpleaudio = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import simpleaudio as sa
except Exception:  # pragma: no cover - optional dependency
    sa = None  # type: ignore

logger = logging.getLogger(__name__)


def _has_ffmpeg() -> bool:
    """Return ``True`` when ``ffmpeg`` is available on the system path."""
    return shutil.which("ffmpeg") is not None


_loops: list[Thread] = []
_playbacks: list[Any] = []
_stop_event = Event()


_ASSET_DIR = Path(__file__).resolve().parent / "MUSIC_FOUNDATION" / "sound_assets"


def get_asset_path(
    name: str, *, duration: float = 0.5, frequency: float | None = None
) -> Path:
    """Return path to ``name`` or synthesize a temporary tone if missing."""

    path = _ASSET_DIR / name
    if path.exists():
        return path

    if frequency is None:
        digits = "".join(c for c in Path(name).stem if c.isdigit())
        try:
            frequency = float(digits) if digits else 440.0
        except ValueError:  # pragma: no cover - malformed digits
            frequency = 440.0

    tmp = Path(tempfile.gettempdir()) / name
    if not tmp.exists():
        if sf is None:
            raise RuntimeError("soundfile library not installed")
        tone = generate_tone(frequency, duration)
        sf.write(tmp, tone, 44100)
    return tmp


def _loop_play(audio: Any) -> None:
    """Continuously play ``audio`` until ``stop_all`` is called."""
    while not _stop_event.is_set():
        pb = _play_segment(audio)
        _playbacks.append(pb)
        pb.wait_done()


def _loop_play_n(audio: Any, loops: int) -> None:
    """Play ``audio`` ``loops`` times unless stopped."""
    for _ in range(loops):
        if _stop_event.is_set():
            break
        pb = _play_segment(audio)
        _playbacks.append(pb)
        pb.wait_done()


def _play_segment(seg: Any) -> Any:
    """Play ``seg`` using the appropriate backend."""
    if _play_with_simpleaudio is not None and not hasattr(seg, "data"):
        return _play_with_simpleaudio(seg)
    if sa is None:
        raise RuntimeError("simpleaudio library not installed")
    if not hasattr(seg, "data"):
        raise TypeError("unsupported audio segment type")
    data = seg.data
    sr = seg.frame_rate
    arr = np.int16(np.clip(data, -1, 1) * 32767)
    channels = arr.shape[1] if arr.ndim > 1 else 1  # type: ignore[misc]
    return sa.play_buffer(arr, channels, 2, sr)


def play_sound(path: Path, loop: bool = False, *, loops: int | None = None) -> None:
    """Play an audio file optionally in a loop.

    Parameters
    ----------
    path:
        File path to the audio sample.
    loop:
        When ``True`` the sample repeats until :func:`stop_all` is called.
    loops:
        Number of times to play the sample. Ignored when ``loop`` is ``True``.
    """
    if AudioSegment is None:
        logger.warning("audio backend not available; cannot play audio")
        return
    if not _has_ffmpeg():
        logger.warning("ffmpeg not installed; cannot play audio")
        return
    audio = AudioSegment.from_file(path)
    if loop:
        thread = Thread(target=_loop_play, args=(audio,), daemon=True)
        _loops.append(thread)
        thread.start()
    elif loops and loops > 1:
        thread = Thread(target=_loop_play_n, args=(audio, loops), daemon=True)
        _loops.append(thread)
        thread.start()
    else:
        pb = _play_segment(audio)
        _playbacks.append(pb)
        pb.wait_done()


def stop_all() -> None:
    """Stop all currently playing sounds and loops."""
    _stop_event.set()
    for pb in list(_playbacks):
        try:
            pb.stop()
        except Exception as exc:  # pragma: no cover - optional playback object
            logger.debug("playback object lacks stop(): %s", exc)
    _playbacks.clear()
    for thread in list(_loops):
        thread.join(timeout=0.1)
    _loops.clear()
    _stop_event.clear()


__all__ = [
    "play_sound",
    "stop_all",
    "get_asset_path",
    "pitch_shift",
    "time_stretch",
    "compress",
    "rave_encode",
    "rave_decode",
    "rave_morph",
    "nsynth_interpolate",
]
