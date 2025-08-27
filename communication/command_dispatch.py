from __future__ import annotations

"""Command dispatch microservice with event mirroring.

Operator directives are validated and routed to registered agents. Commands sent
through critical channels are mirrored to an immutable storage directory. The
service exposes an endpoint to verify mirrored events.
"""

import json
import uuid
from pathlib import Path
from typing import Callable, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# Channels requiring event mirroring
CRITICAL_CHANNELS = {"ops", "safety"}

# Storage location for mirrored events
STORAGE_DIR = Path("event_mirror")

Handler = Callable[[str], None]

_dispatch_registry: Dict[str, Handler] = {}
app = FastAPI(title="Command Dispatch Service")


class Directive(BaseModel):
    """Instruction from an operator targeting an agent."""

    operator: str = Field(min_length=1)
    agent: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    command: str = Field(min_length=1)


def register_agent(name: str, handler: Handler) -> None:
    """Register ``handler`` for ``name``."""

    _dispatch_registry[name] = handler


def _mirror_event(event_id: str, directive: Directive) -> None:
    """Write ``directive`` to a read-only file under its channel."""

    channel_dir = STORAGE_DIR / directive.channel
    channel_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "event_id": event_id,
        "operator": directive.operator,
        "agent": directive.agent,
        "channel": directive.channel,
        "command": directive.command,
    }
    dest = channel_dir / f"{event_id}.json"
    dest.write_text(json.dumps(record))
    dest.chmod(0o444)


@app.post("/dispatch")
async def dispatch_directive(directive: Directive) -> dict[str, str]:
    """Validate ``directive`` and route it to its agent."""

    handler = _dispatch_registry.get(directive.agent)
    if handler is None:
        raise HTTPException(status_code=404, detail="unknown agent")
    handler(directive.command)
    event_id = uuid.uuid4().hex
    if directive.channel in CRITICAL_CHANNELS:
        _mirror_event(event_id, directive)
    return {"event_id": event_id}


@app.get("/verify/{event_id}")
async def verify_event(event_id: str) -> dict:
    """Return mirrored event ``event_id`` if available."""

    for path in STORAGE_DIR.rglob(f"{event_id}.json"):
        return json.loads(path.read_text())
    raise HTTPException(status_code=404, detail="event not found")


__all__ = ["app", "register_agent", "CRITICAL_CHANNELS"]
