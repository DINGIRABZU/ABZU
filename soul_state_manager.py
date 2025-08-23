"""Track the active archetype and soul state transitions."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict

STATE_FILE = Path("data/soul_state_tracker.json")

_DEFAULT_STATE = {"archetype": None, "soul_state": None}
_STATE: Dict[str, Any] = {}
_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


def _load_state() -> None:
    """Load persisted state into :data:`_STATE`."""
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


def get_state() -> Dict[str, Any]:
    """Return a copy of the current soul state tracker."""
    with _LOCK:
        return dict(_STATE)


def update_soul_state(state: str | None) -> None:
    """Set ``state`` as the current soul state."""
    with _LOCK:
        _STATE["soul_state"] = state
    _save_state()
    logger.info("soul_state updated to %s", state)


def update_archetype(archetype: str | None) -> None:
    """Set ``archetype`` as the active archetype."""
    with _LOCK:
        _STATE["archetype"] = archetype
    _save_state()


async def get_state_async() -> Dict[str, Any]:
    """Asynchronous wrapper for :func:`get_state`."""
    return await asyncio.to_thread(get_state)


async def update_soul_state_async(state: str | None) -> None:
    """Asynchronous wrapper for :func:`update_soul_state`."""
    await asyncio.to_thread(update_soul_state, state)


async def update_archetype_async(archetype: str | None) -> None:
    """Asynchronous wrapper for :func:`update_archetype`."""
    await asyncio.to_thread(update_archetype, archetype)
    logger.info("archetype updated to %s", archetype)


__all__ = [
    "get_state",
    "update_soul_state",
    "update_archetype",
    "get_state_async",
    "update_soul_state_async",
    "update_archetype_async",
]
