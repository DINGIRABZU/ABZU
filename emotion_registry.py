"""Persist emotional state and expose retrieval helpers.

State is stored on disk under ``data/emotion_state.json`` and updated through
the module's helper functions.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict

STATE_FILE = Path("data/emotion_state.json")
_DEFAULT_STATE = {
    "current_layer": None,
    "last_emotion": None,
    "resonance_level": 0.0,
    "preferred_expression_channel": "text",
}
_STATE: Dict[str, Any] = {}
_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


def _load_state() -> None:
    """Load state from :data:`STATE_FILE` into :data:`_STATE`."""
    global _STATE
    with _LOCK:
        if STATE_FILE.exists():
            try:
                _STATE = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                _STATE = _DEFAULT_STATE.copy()
        else:
            _STATE = _DEFAULT_STATE.copy()


def _save_state() -> None:
    """Write :data:`_STATE` to :data:`STATE_FILE`."""
    with _LOCK:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(_STATE, indent=2), encoding="utf-8")


_load_state()


def get_current_layer() -> str | None:
    """Return the active personality layer name if set."""
    with _LOCK:
        return _STATE.get("current_layer")


def set_current_layer(layer: str | None) -> None:
    """Set ``layer`` as the active personality layer."""
    with _LOCK:
        _STATE["current_layer"] = layer
    _save_state()
    logger.info("current_layer set to %s", layer)


def get_last_emotion() -> str | None:
    """Return the most recently observed emotion."""
    with _LOCK:
        return _STATE.get("last_emotion")


def set_last_emotion(emotion: str | None) -> None:
    """Record ``emotion`` as the last observed emotion."""
    with _LOCK:
        _STATE["last_emotion"] = emotion
    _save_state()
    logger.info("last_emotion set to %s", emotion)


def get_resonance_level() -> float:
    """Return the current resonance level."""
    with _LOCK:
        return float(_STATE.get("resonance_level", 0.0))


def set_resonance_level(level: float) -> None:
    """Set the emotional resonance ``level``."""
    with _LOCK:
        _STATE["resonance_level"] = float(level)
    _save_state()
    logger.info("resonance_level set to %.3f", level)


def get_preferred_expression_channel() -> str:
    """Return the preferred expression channel."""
    with _LOCK:
        return str(_STATE.get("preferred_expression_channel", "text"))


def set_preferred_expression_channel(channel: str) -> None:
    """Persist the preferred expression ``channel``."""
    with _LOCK:
        _STATE["preferred_expression_channel"] = channel
    _save_state()
    logger.info("preferred_channel set to %s", channel)


async def get_current_layer_async() -> str | None:
    """Asynchronous wrapper for :func:`get_current_layer`."""
    return await asyncio.to_thread(get_current_layer)


async def set_current_layer_async(layer: str | None) -> None:
    """Asynchronous wrapper for :func:`set_current_layer`."""
    await asyncio.to_thread(set_current_layer, layer)


async def get_last_emotion_async() -> str | None:
    """Asynchronous wrapper for :func:`get_last_emotion`."""
    return await asyncio.to_thread(get_last_emotion)


async def set_last_emotion_async(emotion: str | None) -> None:
    """Asynchronous wrapper for :func:`set_last_emotion`."""
    await asyncio.to_thread(set_last_emotion, emotion)


async def get_resonance_level_async() -> float:
    """Asynchronous wrapper for :func:`get_resonance_level`."""
    return await asyncio.to_thread(get_resonance_level)


async def set_resonance_level_async(level: float) -> None:
    """Asynchronous wrapper for :func:`set_resonance_level`."""
    await asyncio.to_thread(set_resonance_level, level)


async def get_preferred_expression_channel_async() -> str:
    """Asynchronous wrapper for :func:`get_preferred_expression_channel`."""
    return await asyncio.to_thread(get_preferred_expression_channel)


async def set_preferred_expression_channel_async(channel: str) -> None:
    """Asynchronous wrapper for :func:`set_preferred_expression_channel`."""
    await asyncio.to_thread(set_preferred_expression_channel, channel)


__all__ = [
    "get_current_layer",
    "set_current_layer",
    "get_last_emotion",
    "set_last_emotion",
    "get_resonance_level",
    "set_resonance_level",
    "get_preferred_expression_channel",
    "set_preferred_expression_channel",
    "get_current_layer_async",
    "set_current_layer_async",
    "get_last_emotion_async",
    "set_last_emotion_async",
    "get_resonance_level_async",
    "set_resonance_level_async",
    "get_preferred_expression_channel_async",
    "set_preferred_expression_channel_async",
]
