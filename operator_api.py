"""Operator command API exposing the :class:`OperatorDispatcher`.

- **Endpoints:** ``POST /operator/command``, ``POST /operator/upload``
- **Auth:** Bearer token
- **Linked agents:** Orchestration Master via Crown, RAZAR
"""

from __future__ import annotations

__version__ = "0.3.4"

import json
import logging
import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)

from agents.operator_dispatcher import OperatorDispatcher

logger = logging.getLogger(__name__)

router = APIRouter()
_dispatcher = OperatorDispatcher(
    {
        "overlord": ["cocytus", "victim", "crown"],
        "auditor": ["victim"],
        "crown": ["razar"],
    }
)

_event_clients: set[WebSocket] = set()


async def broadcast_event(event: dict[str, object]) -> None:
    """Send ``event`` to all connected operator event clients."""
    message = json.dumps(event)
    for ws in set(_event_clients):
        try:
            await ws.send_text(message)
        except Exception:  # pragma: no cover - network failure
            _event_clients.discard(ws)


@router.websocket("/operator/events")
async def operator_events(websocket: WebSocket) -> None:
    """WebSocket channel streaming command acknowledgements and progress."""
    await websocket.accept()
    _event_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _event_clients.discard(websocket)


@router.post("/operator/command")
async def dispatch_command(data: dict[str, str]) -> dict[str, object]:
    """Dispatch an operator command to a target agent."""
    operator = data.get("operator", "")
    agent = data.get("agent", "")
    command_name = data.get("command", "")
    if not operator or not agent or not command_name:
        raise HTTPException(
            status_code=400, detail="operator, agent and command required"
        )

    def _noop() -> dict[str, str]:
        return {"ack": command_name}

    await broadcast_event({"event": "ack", "command": command_name})

    try:
        result = _dispatcher.dispatch(operator, agent, _noop)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - dispatcher failure
        logger.error("dispatch failed: %s", exc)
        raise HTTPException(status_code=500, detail="dispatch failed") from exc

    await broadcast_event(
        {"event": "progress", "command": command_name, "percent": 100}
    )

    return {"result": result}


@router.post("/operator/upload")
async def upload_file(
    operator: str = Form(...),
    metadata: str = Form("{}"),
    files: list[UploadFile] | None = File(None),
) -> dict[str, object]:
    """Store uploaded ``files`` and forward ``metadata`` to RAZAR via Crown.

    ``files`` may be empty, allowing metadata-only uploads that are still
    relayed to Crown for context.
    """
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid metadata") from exc

    upload_dir = Path("uploads") / operator
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored: list[str] = []
    for item in files or []:
        dest = upload_dir / item.filename
        try:
            with dest.open("wb") as fh:
                shutil.copyfileobj(item.file, fh)
            stored.append(str(dest.relative_to(Path("uploads"))))
            await broadcast_event(
                {
                    "event": "progress",
                    "command": "upload",
                    "file": item.filename,
                }
            )
        except Exception as exc:  # pragma: no cover - disk failure
            logger.error("failed to store %s: %s", item.filename, exc)
            raise HTTPException(status_code=500, detail="failed to store file") from exc

    def _relay(meta: dict[str, object]) -> dict[str, object]:
        """Crown forwards metadata and stored paths to RAZAR."""

        def _send(m: dict[str, object]) -> dict[str, object]:
            return {"received": m, "files": stored}

        return _dispatcher.dispatch("crown", "razar", _send, meta)

    meta_with_files = {**meta, "files": stored}

    try:
        _dispatcher.dispatch(operator, "crown", _relay, meta_with_files)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - dispatcher failure
        logger.error("metadata relay failed: %s", exc)
        raise HTTPException(status_code=500, detail="relay failed") from exc

    await broadcast_event(
        {
            "event": "progress",
            "command": "upload",
            "percent": 100,
            "files": stored,
        }
    )

    return {"stored": stored, "metadata": meta_with_files}


__all__ = ["router"]
