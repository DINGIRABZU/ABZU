from __future__ import annotations

"""Speech synthesis wrapper that optionally routes audio via a connector."""

from typing import Callable, Optional

from INANNA_AI import tts_coqui

from . import context_tracker

AudioCallback = Callable[[str], None]

_audio_callback: AudioCallback | None = None
_connector: Optional[object] = None


def register_audio_callback(func: AudioCallback) -> None:
    """Set ``func`` to be called with the synthesized audio path."""
    global _audio_callback
    _audio_callback = func


def register_connector(connector: object) -> None:
    """Store ``connector`` used for call routing."""
    global _connector
    _connector = connector


def synthesize_speech(text: str, emotion: str) -> str:
    """Generate speech and route it via the active callback."""
    path = tts_coqui.synthesize_speech(text, emotion)
    if context_tracker.state.in_call and _connector is not None:
        start = getattr(_connector, "start_call", None)
        if callable(start):
            start(path)
    if _audio_callback is not None:
        _audio_callback(path)
    return path


__all__ = ["register_audio_callback", "register_connector", "synthesize_speech"]
