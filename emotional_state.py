from __future__ import annotations

"""Persist and retrieve emotional and soul state parameters."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import soul_state_manager

STATE_FILE = Path("data/emotion_state.json")
REGISTRY_FILE = Path("data/emotion_registry.json")
_DEFAULT_STATE = {
    "current_layer": None,
    "last_emotion": None,
    "resonance_level": 0.0,
    "preferred_expression_channel": "text",
    "resonance_pairs": [],
    "soul_state": None,
}
_STATE: Dict[str, Any] = {}
_REGISTRY: List[str] = []

logger = logging.getLogger(__name__)


def _load_state() -> None:
    """Load state from :data:`STATE_FILE` into :data:`_STATE`."""
    global _STATE
    if STATE_FILE.exists():
        try:
            _STATE = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _STATE = _DEFAULT_STATE.copy()
    else:
        _STATE = _DEFAULT_STATE.copy()


def _save_state() -> None:
    """Write :data:`_STATE` to :data:`STATE_FILE`."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(_STATE, indent=2), encoding="utf-8")


def _load_registry() -> None:
    """Populate :data:`_REGISTRY` from :data:`REGISTRY_FILE`."""

    global _REGISTRY
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
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(_REGISTRY, indent=2), encoding="utf-8")


def _ensure_in_registry(emotion: str) -> None:
    """Add ``emotion`` to the registry if not already present."""
    if emotion and emotion not in _REGISTRY:
        _REGISTRY.append(emotion)
        _save_registry()


_load_state()
_load_registry()


def get_current_layer() -> str | None:
    """Return the active personality layer name if set."""
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
    _STATE["current_layer"] = layer
    _save_state()
    logger.info("current_layer set to %s", layer)


def get_last_emotion() -> str | None:
    """Return the most recently observed emotion."""
    return _STATE.get("last_emotion")


def set_last_emotion(emotion: str | None) -> None:
    """Record ``emotion`` as the last observed emotion."""
    _STATE["last_emotion"] = emotion
    _save_state()
    if emotion is not None:
        _ensure_in_registry(emotion)
    logger.info("last_emotion set to %s", emotion)


def get_resonance_level() -> float:
    """Return the current resonance level."""
    return float(_STATE.get("resonance_level", 0.0))


def set_resonance_level(level: float) -> None:
    """Set the emotional resonance ``level``."""
    _STATE["resonance_level"] = float(level)
    _save_state()
    logger.info("resonance_level set to %.3f", level)


def get_preferred_expression_channel() -> str:
    """Return the preferred expression channel."""
    return str(_STATE.get("preferred_expression_channel", "text"))


def set_preferred_expression_channel(channel: str) -> None:
    """Persist the preferred expression ``channel``."""
    _STATE["preferred_expression_channel"] = channel
    _save_state()
    logger.info("preferred_channel set to %s", channel)


def get_resonance_pairs() -> List[Tuple[float, float]]:
    """Return stored resonance frequency pairs."""
    pairs = _STATE.get("resonance_pairs", [])
    return [(float(a), float(b)) for a, b in pairs]


def set_resonance_pairs(pairs: List[Tuple[float, float]]) -> None:
    """Persist ``pairs`` of resonance frequencies."""
    _STATE["resonance_pairs"] = [[float(a), float(b)] for a, b in pairs]
    _save_state()
    logger.info("resonance_pairs set", extra={"emotion": _STATE.get("last_emotion"), "resonance": _STATE.get("resonance_level")})


def get_soul_state() -> str | None:
    """Return the current soul state."""
    return _STATE.get("soul_state")


def set_soul_state(state: str | None) -> None:
    """Persist the current ``state`` of the soul."""
    _STATE["soul_state"] = state
    _save_state()
    try:
        soul_state_manager.update_soul_state(state)
    except Exception:
        logger.exception("failed to update soul_state_manager")
    logger.info("soul_state set to %s", state)


def get_registered_emotions() -> List[str]:
    """Return the list of known emotion labels."""
    return list(_REGISTRY)


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
]
