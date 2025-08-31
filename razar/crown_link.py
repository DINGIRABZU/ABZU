from __future__ import annotations

__version__ = "0.2.2"

"""WebSocket link between RAZAR and the CROWN agent.

This module implements a tiny WebSocket client used by the external RAZAR
agent to exchange diagnostics with the CROWN LLM stack.  Two message types are
supported:

* ``status`` – notification that a component finished an operation.  The
  payload includes the component name, result (``"ok"``/``"failed"``) and a
  short log snippet.
* ``repair`` – request to repair a failing component.  The payload contains the
  captured stack trace and a configuration summary.  The server is expected to
  reply with patch instructions.

A structured prompt template for the GLM‑4.1V‑9B model is provided via
:func:`build_patch_prompt` which fills the ``PATCH_PROMPT_TEMPLATE`` with error
context.
"""

from dataclasses import asdict, dataclass
import json
import logging
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import websockets
except Exception:  # pragma: no cover - handled at runtime
    websockets = None  # type: ignore

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Message models
# ---------------------------------------------------------------------------
@dataclass
class StatusUpdate:
    """Details about the outcome of a component action."""

    component: str
    result: str
    log_snippet: str


@dataclass
class RepairRequest:
    """Request for automated repair guidance."""

    stack_trace: str
    config_summary: str


# ---------------------------------------------------------------------------
# WebSocket client
# ---------------------------------------------------------------------------
class CrownLink:
    """Minimal WebSocket client for RAZAR ⇆ CROWN communication."""

    def __init__(self, url: str) -> None:
        if websockets is None:  # pragma: no cover - import guard
            raise RuntimeError("websockets package is required to use CrownLink")
        self.url = url
        self._ws: websockets.client.WebSocketClientProtocol | None = None

    async def __aenter__(self) -> "CrownLink":
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        """Establish the WebSocket connection."""

        LOGGER.debug("Connecting to %s", self.url)
        self._ws = await websockets.connect(self.url)

    async def close(self) -> None:
        """Close the WebSocket connection if open."""

        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    async def _send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._ws is None:
            await self.connect()
        assert self._ws is not None  # for type checkers
        await self._ws.send(json.dumps(payload))
        reply = await self._ws.recv()
        try:
            return json.loads(reply)
        except json.JSONDecodeError:  # pragma: no cover - passthrough
            return {"raw": reply}

    async def send_status_update(self, update: StatusUpdate) -> Dict[str, Any]:
        """Send ``update`` and return the decoded response."""

        payload = {"type": "status", **asdict(update)}
        return await self._send(payload)

    async def send_repair_request(self, request: RepairRequest) -> Dict[str, Any]:
        """Send ``request`` and return the decoded response."""

        payload = {"type": "repair", **asdict(request)}
        return await self._send(payload)


# ---------------------------------------------------------------------------
# Prompt template for GLM‑4.1V‑9B
# ---------------------------------------------------------------------------
PATCH_PROMPT_TEMPLATE = (
    """You are GLM-4.1V-9B tasked with repairing a failing component.\n\n"""
    "Component: {component}\n"
    "Stack trace:\n{stack_trace}\n"
    "Configuration summary:\n{config_summary}\n\n"
    "Reply with JSON containing:\n"
    "- patch: unified diff applying the fix\n"
    "- tests: list of commands to verify the patch\n"
    "- notes: brief rationale for the change"
    ""
)


def build_patch_prompt(component: str, stack_trace: str, config_summary: str) -> str:
    """Return the patch request prompt for GLM‑4.1V‑9B."""

    return PATCH_PROMPT_TEMPLATE.format(
        component=component, stack_trace=stack_trace, config_summary=config_summary
    )


__all__ = [
    "CrownLink",
    "StatusUpdate",
    "RepairRequest",
    "build_patch_prompt",
    "PATCH_PROMPT_TEMPLATE",
]
