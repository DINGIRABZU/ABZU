from __future__ import annotations

"""Simple playback engine for ritual loops and voice audio."""

from pathlib import Path
from threading import Event, Thread
from typing import Any
import logging
import tempfile
from io import BytesIO
import base64

import numpy as np
import soundfile as sf
from MUSIC_FOUNDATION.layer_generators import generate_tone
from dsp_engine import (
    pitch_shift,
    time_stretch,
    compress,
    rave_encode,
    rave_decode,
    rave_morph,
    nsynth_interpolate,
)

try:  # pragma: no cover - optional dependency
    from pydub import AudioSegment
    from pydub.playback import _play_with_simpleaudio
except Exception:  # pragma: no cover - optional dependency
    AudioSegment = None  # type: ignore
    _play_with_simpleaudio = None  # type: ignore

logger = logging.getLogger(__name__)

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
        tone = generate_tone(frequency, duration)
        sf.write(tmp, tone, 44100)
    return tmp


def _loop_play(audio: Any) -> None:
    """Continuously play ``audio`` until ``stop_all`` is called."""
    while not _stop_event.is_set():
        pb = _play_with_simpleaudio(audio)
        _playbacks.append(pb)
        pb.wait_done()


def _loop_play_n(audio: Any, loops: int) -> None:
    """Play ``audio`` ``loops`` times unless stopped."""
    for _ in range(loops):
        if _stop_event.is_set():
            break
        pb = _play_with_simpleaudio(audio)
        _playbacks.append(pb)
        pb.wait_done()


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
    if AudioSegment is None or _play_with_simpleaudio is None:
        logger.warning("pydub not installed; cannot play audio")
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
        pb = _play_with_simpleaudio(audio)
        _playbacks.append(pb)
        pb.wait_done()


def stop_all() -> None:
    """Stop all currently playing sounds and loops."""
    _stop_event.set()
    for pb in list(_playbacks):
        try:
            pb.stop()
        except Exception:  # pragma: no cover - optional playback object
            pass
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
