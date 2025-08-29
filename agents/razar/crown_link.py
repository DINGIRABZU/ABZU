from __future__ import annotations

__version__ = "0.1.0"

"""Communication link between the RAZAR agent and CROWN.

This module implements a tiny WebSocket client used by the development
``agents.razar`` toolkit to exchange diagnostic information with the CROWN
stack.  RAZAR transmits a blueprint excerpt and failure log to CROWN, which in
turn replies with code suggestions or architectural revisions.  Every request
and response pair is recorded as a JSON line under
``logs/razar_crown_dialogues.json`` for later inspection.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import websockets
except Exception:  # pragma: no cover - handled at runtime
    websockets = None  # type: ignore

LOGGER = logging.getLogger(__name__)
# Persist dialogue history under the repository's ``logs`` directory
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "razar_crown_dialogues.json"


# ---------------------------------------------------------------------------
# Message models
# ---------------------------------------------------------------------------
@dataclass
class BlueprintReport:
    """Payload sent from RAZAR describing a failure."""

    blueprint_excerpt: str
    failure_log: str


@dataclass
class StatusUpdate:
    """Runtime health update sent to CROWN or servant models."""

    component: str
    result: str
    log_snippet: str | None = None


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
            data = json.loads(reply)
        except json.JSONDecodeError:  # pragma: no cover - passthrough
            data = {"raw": reply}
        self._log_dialogue(payload, data)
        return data

    async def send_report(self, report: BlueprintReport) -> Dict[str, Any]:
        """Send ``report`` to CROWN and return the decoded response."""

        payload = {"type": "report", **asdict(report)}
        return await self._send(payload)

    async def send_status(self, update: StatusUpdate) -> Dict[str, Any]:
        """Send a status update to CROWN or a servant model."""

        payload = {"type": "status", **asdict(update)}
        return await self._send(payload)

    # ``exchange`` is kept for backward compatibility
    exchange = send_report

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log_dialogue(self, request: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Append the request/response pair to ``LOG_PATH``."""

        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": request,
            "response": response,
        }
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


__all__ = ["CrownLink", "BlueprintReport", "StatusUpdate", "LOG_PATH"]
