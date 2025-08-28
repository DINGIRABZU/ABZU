from __future__ import annotations

"""Basic recovery manager coordinating shutdown, patching and resumption.

The real system uses a message bus and remote code repair agents.  For the
purposes of this repository we persist a minimal audit trail under the
``recovery_state`` directory so unit tests can assert behaviour without the
runtime infrastructure.
"""

from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
from typing import Any, Dict

LOGGER = logging.getLogger(__name__)

STATE_DIR = Path(__file__).resolve().parents[1] / "recovery_state"


@dataclass
class PatchInfo:
    """Details describing a patch to apply to a component."""

    description: str
    diff: str | None = None
    tests: list[str] | None = None


def _record(component: str, action: str, data: Dict[str, Any] | None = None) -> None:
    """Persist an ``action`` for ``component`` to :data:`STATE_DIR`.

    Each action is written to ``<component>_<action>.json`` so tests can verify
    the recovery sequence.  The directory is created on first use.
    """

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"{component}_{action}.json"
    payload = {"component": component, "action": action, "data": data or {}}
    path.write_text(json.dumps(payload, indent=2))


def request_shutdown(component: str) -> None:
    """Record a shutdown request for ``component``.

    In a full implementation this would signal the component over the
    lifecycle bus.  Here we simply log and persist the request.
    """

    LOGGER.info("Requesting shutdown for %s", component)
    _record(component, "shutdown")


def apply_patch(component: str, patch_info: PatchInfo | Dict[str, Any]) -> None:
    """Persist ``patch_info`` for ``component`` and log the operation."""

    if not isinstance(patch_info, PatchInfo):
        patch_info = PatchInfo(**patch_info)  # type: ignore[arg-type]
    LOGGER.info("Applying patch for %s: %s", component, patch_info.description)
    _record(component, "patch", asdict(patch_info))


def resume(component: str) -> None:
    """Record resumption of ``component`` after patching."""

    LOGGER.info("Resuming component %s", component)
    _record(component, "resume")


__all__ = ["PatchInfo", "request_shutdown", "apply_patch", "resume"]
