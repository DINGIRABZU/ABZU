"""WebSocket handshake between RAZAR and the CROWN stack.

This module sends a mission brief to the CROWN agent and awaits an
acknowledgment containing the capabilities available for the current
session.  Every exchange is appended to ``logs/razar_crown_dialogues.json``
so operators can audit the dialogue later.
"""

from __future__ import annotations

__version__ = "0.2.5"

from dataclasses import asdict, dataclass
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import recovery_manager

try:  # pragma: no cover - optional dependency
    import websockets
except Exception:  # pragma: no cover - handled at runtime
    websockets = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass
class MissionBrief:
    """Details sent from RAZAR before the boot cycle."""

    priority_map: Dict[str, int]
    current_status: Dict[str, str]
    open_issues: List[str]


@dataclass
class CrownResponse:
    """Acknowledgment and capabilities from the CROWN stack."""

    acknowledgement: str
    capabilities: List[str]
    downtime: Dict[str, Any]
    identity_fingerprint: Optional[Dict[str, Any]] = None


DEFAULT_TRANSCRIPT_PATH = Path("logs/razar_crown_dialogues.json")


class CrownHandshake:
    """Perform the RAZAR ⇆ CROWN mission brief exchange."""

    def __init__(
        self,
        url: str,
        transcript_path: str | Path = DEFAULT_TRANSCRIPT_PATH,
    ) -> None:
        if websockets is None:  # pragma: no cover - import guard
            raise RuntimeError("websockets package is required to use CrownHandshake")
        self.url = url
        self.transcript_path = Path(transcript_path)

    def _load_transcripts(self) -> List[Dict[str, Any]]:
        if self.transcript_path.exists():
            try:
                return json.loads(self.transcript_path.read_text())
            except json.JSONDecodeError:  # pragma: no cover - default empty
                return []
        return []

    def _append_transcript(self, role: str, message: Dict[str, Any]) -> None:
        transcripts = self._load_transcripts()
        transcripts.append({"role": role, "message": message})
        self.transcript_path.parent.mkdir(parents=True, exist_ok=True)
        self.transcript_path.write_text(json.dumps(transcripts, indent=2))

    def _log_patch_action(
        self, archive_dir: Path, component: str, patch: Dict[str, Any]
    ) -> None:
        """Archive patch details alongside mission briefs."""
        archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        path = archive_dir / f"{timestamp}_{component}_patch.json"
        path.write_text(json.dumps({"component": component, "patch": patch}, indent=2))

    async def perform(self, mission_brief_path: str) -> CrownResponse:
        """Send ``mission_brief_path`` and return the CROWN acknowledgment."""

        brief_data = json.loads(Path(mission_brief_path).read_text())
        brief = MissionBrief(**brief_data)
        self._append_transcript("razar", asdict(brief))

        LOGGER.debug("Connecting to %s", self.url)
        async with websockets.connect(self.url) as ws:
            await ws.send(json.dumps(asdict(brief)))
            reply_raw = await ws.recv()

        try:
            reply = json.loads(reply_raw)
        except json.JSONDecodeError:  # pragma: no cover - passthrough
            reply = {"raw": reply_raw}

        fingerprint_raw = os.getenv("CROWN_IDENTITY_FINGERPRINT")
        fingerprint: Optional[Dict[str, Any]]
        if fingerprint_raw:
            try:
                parsed = json.loads(fingerprint_raw)
                if isinstance(parsed, dict):
                    fingerprint = parsed
                else:  # pragma: no cover - unexpected payload shape
                    fingerprint = {"value": fingerprint_raw}
            except json.JSONDecodeError:  # pragma: no cover - legacy payloads
                fingerprint = {"value": fingerprint_raw}
        else:
            fingerprint = None

        transcript_payload = dict(reply)
        if fingerprint is not None:
            transcript_payload["identity_fingerprint"] = fingerprint
        self._append_transcript("crown", transcript_payload)

        downtime = reply.get("downtime", {})
        archive_dir = Path(mission_brief_path).resolve().parent
        for component, patch in downtime.items():
            recovery_manager.request_shutdown(component)
            if patch:
                recovery_manager.apply_patch(component, patch)
                self._log_patch_action(archive_dir, component, patch)
            recovery_manager.resume(component)

        return CrownResponse(
            acknowledgement=reply.get("ack", ""),
            capabilities=reply.get("capabilities", []),
            downtime=downtime,
            identity_fingerprint=fingerprint,
        )


async def perform(
    mission_brief_path: str,
    *,
    url: str | None = None,
    transcript_path: str | Path = DEFAULT_TRANSCRIPT_PATH,
) -> CrownResponse:
    """Convenience wrapper to execute a handshake and return the response."""
    url = url or os.environ["CROWN_WS_URL"]
    handshake = CrownHandshake(url, transcript_path)
    return await handshake.perform(mission_brief_path)


__all__ = [
    "MissionBrief",
    "CrownResponse",
    "CrownHandshake",
    "perform",
]
