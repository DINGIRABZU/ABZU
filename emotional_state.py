"""Persist and retrieve emotional and soul state parameters."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:  # pragma: no cover - optional dependency
    import soul_state_manager
except Exception:  # pragma: no cover - optional dependency
    soul_state_manager = None  # type: ignore

STATE_FILE = Path("data/emotion_state.json")
REGISTRY_FILE = Path("data/emotion_registry.json")
EVENT_LOG = Path("data/emotion_events.jsonl")
_DEFAULT_STATE: Dict[str, Any] = {
    "current_layer": None,
    "last_emotion": None,
    "resonance_level": 0.0,
    "preferred_expression_channel": "text",
    "resonance_pairs": [],
    "soul_state": None,
}
_STATE: Dict[str, Any] = {}
_REGISTRY: List[str] = []
_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


def _log_event(event: str, **payload: Any) -> None:
    """Append a structured emotion event to :data:`EVENT_LOG`."""
    try:
        EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": event,
            **payload,
        }
        EVENT_LOG.open("a", encoding="utf-8").write(json.dumps(entry) + "\n")
    except Exception:  # pragma: no cover - best effort
        logger.exception("failed to write emotion event")


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


def _load_registry() -> None:
    """Populate :data:`_REGISTRY` from :data:`REGISTRY_FILE`."""
    global _REGISTRY
    with _LOCK:
        if REGISTRY_FILE.exists():
            try:
                data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    unique = {str(e) for e in data}
                    _REGISTRY = sorted(unique)
                else:
                    _REGISTRY = []
            except Exception:
                _REGISTRY = []
        else:
            _REGISTRY = []


def _save_registry() -> None:
    """Persist :data:`_REGISTRY` to :data:`REGISTRY_FILE`."""
    with _LOCK:
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY_FILE.write_text(json.dumps(_REGISTRY, indent=2), encoding="utf-8")


def _ensure_in_registry(emotion: str) -> None:
    """Add ``emotion`` to the registry if not already present."""
    with _LOCK:
        if emotion and emotion not in _REGISTRY:
            _REGISTRY.append(emotion)
            _save_registry()


_load_state()
_load_registry()


def get_current_layer() -> str | None:
    """Return the active personality layer name if set."""
    with _LOCK:
        return _STATE.get("current_layer")


_ALLOWED_LAYERS = {
    "nigredo_layer",
    "albedo_layer",
    "rubedo_layer",
    "citrinitas_layer",
}


def set_current_layer(layer: str | None) -> None:
    """Set ``layer`` as the active personality layer."""
    if layer is not None and layer not in _ALLOWED_LAYERS:
        raise ValueError(f"unknown layer: {layer}")
    with _LOCK:
        _STATE["current_layer"] = layer
    _save_state()
    logger.info("current_layer set to %s", layer)
    _log_event("set_current_layer", layer=layer)


def get_last_emotion() -> str | None:
    """Return the most recently observed emotion."""
    with _LOCK:
        return _STATE.get("last_emotion")


def set_last_emotion(emotion: str | None) -> None:
    """Record ``emotion`` as the last observed emotion."""
    with _LOCK:
        _STATE["last_emotion"] = emotion
    _save_state()
    if emotion is not None:
        _ensure_in_registry(emotion)
    logger.info("last_emotion set to %s", emotion)
    _log_event("set_last_emotion", emotion=emotion)


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
    _log_event("set_resonance_level", level=float(level))


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
    _log_event("set_preferred_expression_channel", channel=channel)


def get_resonance_pairs() -> List[Tuple[float, float]]:
    """Return stored resonance frequency pairs."""
    with _LOCK:
        pairs = _STATE.get("resonance_pairs", [])
        return [(float(a), float(b)) for a, b in pairs]


def set_resonance_pairs(pairs: List[Tuple[float, float]]) -> None:
    """Persist ``pairs`` of resonance frequencies."""
    with _LOCK:
        _STATE["resonance_pairs"] = [[float(a), float(b)] for a, b in pairs]
    _save_state()
    logger.info(
        "resonance_pairs set",
        extra={
            "emotion": _STATE.get("last_emotion"),
            "resonance": _STATE.get("resonance_level"),
        },
    )
    _log_event("set_resonance_pairs", pairs=pairs)


def get_soul_state() -> str | None:
    """Return the current soul state."""
    with _LOCK:
        return _STATE.get("soul_state")


def set_soul_state(state: str | None) -> None:
    """Persist the current ``state`` of the soul."""
    with _LOCK:
        _STATE["soul_state"] = state
    _save_state()
    if soul_state_manager is not None:
        try:
            soul_state_manager.update_soul_state(state)
        except Exception:
            logger.exception("failed to update soul_state_manager")
    logger.info("soul_state set to %s", state)
    _log_event("set_soul_state", state=state)


def get_registered_emotions() -> List[str]:
    """Return the list of known emotion labels."""
    with _LOCK:
        return list(_REGISTRY)


def snapshot(path: Path | str) -> None:
    """Write state and registry to ``path``."""
    with _LOCK:
        data = {"state": _STATE, "registry": _REGISTRY}
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def restore(path: Path | str) -> None:
    """Load state and registry from ``path`` and persist them."""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    global _STATE, _REGISTRY
    with _LOCK:
        _STATE = dict(data.get("state", _DEFAULT_STATE))
        _REGISTRY = list(data.get("registry", []))
    _save_state()
    _save_registry()


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


async def get_resonance_pairs_async() -> List[Tuple[float, float]]:
    """Asynchronous wrapper for :func:`get_resonance_pairs`."""
    return await asyncio.to_thread(get_resonance_pairs)


async def set_resonance_pairs_async(pairs: List[Tuple[float, float]]) -> None:
    """Asynchronous wrapper for :func:`set_resonance_pairs`."""
    await asyncio.to_thread(set_resonance_pairs, pairs)


async def get_soul_state_async() -> str | None:
    """Asynchronous wrapper for :func:`get_soul_state`."""
    return await asyncio.to_thread(get_soul_state)


async def set_soul_state_async(state: str | None) -> None:
    """Asynchronous wrapper for :func:`set_soul_state`."""
    await asyncio.to_thread(set_soul_state, state)


async def get_registered_emotions_async() -> List[str]:
    """Asynchronous wrapper for :func:`get_registered_emotions`."""
    return await asyncio.to_thread(get_registered_emotions)


async def snapshot_async(path: Path | str) -> None:
    """Asynchronous wrapper for :func:`snapshot`."""
    await asyncio.to_thread(snapshot, path)


async def restore_async(path: Path | str) -> None:
    """Asynchronous wrapper for :func:`restore`."""
    await asyncio.to_thread(restore, path)


__all__ = [
    "get_current_layer",
    "set_current_layer",
    "get_last_emotion",
    "set_last_emotion",
    "get_resonance_level",
    "set_resonance_level",
    "get_preferred_expression_channel",
    "set_preferred_expression_channel",
    "get_resonance_pairs",
    "set_resonance_pairs",
    "get_soul_state",
    "set_soul_state",
    "get_registered_emotions",
    "get_current_layer_async",
    "set_current_layer_async",
    "get_last_emotion_async",
    "set_last_emotion_async",
    "get_resonance_level_async",
    "set_resonance_level_async",
    "get_preferred_expression_channel_async",
    "set_preferred_expression_channel_async",
    "get_resonance_pairs_async",
    "set_resonance_pairs_async",
    "get_soul_state_async",
    "set_soul_state_async",
    "get_registered_emotions_async",
    "snapshot_async",
    "restore_async",
    "snapshot",
    "restore",
    "EVENT_LOG",
]
