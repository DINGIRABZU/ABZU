from __future__ import annotations

"""Coordinate speech synthesis, playback and avatar frames."""

from pathlib import Path
from threading import Thread
from typing import Callable

import numpy as np

from . import language_engine, avatar_expression_engine
import audio_engine

FrameCallback = Callable[[np.ndarray], None]

_frame_callback: FrameCallback | None = None
_background: Path | None = None


def set_frame_callback(func: FrameCallback | None) -> None:
    """Register ``func`` to receive avatar frames."""
    global _frame_callback
    _frame_callback = func


def set_background(path: Path | None) -> None:
    """Set ``path`` as looping background music."""
    global _background
    _background = path


def _handle_audio(path: str) -> None:
    audio_path = Path(path)
    bg_thread = None
    if _background is not None:
        bg_thread = Thread(
            target=audio_engine.play_sound,
            args=(_background,),
            kwargs={"loop": True},
            daemon=True,
        )
        bg_thread.start()

    for frame in avatar_expression_engine.stream_avatar_audio(audio_path):
        if _frame_callback is not None:
            _frame_callback(frame)

    if bg_thread is not None:
        audio_engine.stop_all()
        bg_thread.join()


language_engine.register_audio_callback(_handle_audio)


def speak(text: str, emotion: str) -> Path:
    """Synthesize speech and trigger playback."""
    return Path(language_engine.synthesize_speech(text, emotion))


def play_audio(path: Path, loop: bool = False) -> None:
    """Play ``path`` via the audio engine."""
    audio_engine.play_sound(path, loop=loop)


def make_gif(audio_path: Path, fps: int = 15) -> bytes:
    """Return GIF bytes showing the avatar mouthing ``audio_path``."""
    frames = list(avatar_expression_engine.stream_avatar_audio(audio_path, fps=fps))
    try:
        import imageio.v2 as imageio  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("imageio library required to create GIF") from exc
    return imageio.imwrite(imageio.RETURN_BYTES, frames, format="gif", fps=fps)


__all__ = [
    "speak",
    "set_frame_callback",
    "set_background",
    "play_audio",
    "make_gif",
]
