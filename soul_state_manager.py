from __future__ import annotations

"""Track the active archetype and soul state transitions."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

STATE_FILE = Path("data/soul_state_tracker.json")

_DEFAULT_STATE = {"archetype": None, "soul_state": None}
_STATE: Dict[str, Any] = {}

logger = logging.getLogger(__name__)


def _load_state() -> None:
    """Load persisted state into :data:`_STATE`."""
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


_load_state()


def get_state() -> Dict[str, Any]:
    """Return a copy of the current soul state tracker."""
    return dict(_STATE)


def update_soul_state(state: str | None) -> None:
    """Set ``state`` as the current soul state."""
    _STATE["soul_state"] = state
    _save_state()
    logger.info("soul_state updated to %s", state)


def update_archetype(archetype: str | None) -> None:
    """Set ``archetype`` as the active archetype."""
    _STATE["archetype"] = archetype
    _save_state()
    logger.info("archetype updated to %s", archetype)


__all__ = ["get_state", "update_soul_state", "update_archetype"]
