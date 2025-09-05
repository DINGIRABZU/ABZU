"""Operator command API exposing the :class:`OperatorDispatcher`.

- **Endpoints:** ``POST /operator/command``, ``POST /operator/upload``
- **Auth:** Bearer token
- **Linked agents:** Orchestration Master via Crown, RAZAR
"""

from __future__ import annotations

__version__ = "0.3.5"

import json
import logging
import shutil
from pathlib import Path
from uuid import uuid4
from datetime import datetime

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


def _log_command(entry: dict[str, object]) -> None:
    """Append ``entry`` to ``logs/operator_commands.jsonl``."""
    path = Path("logs") / "operator_commands.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=repr) + "\n")


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
    command_id = str(uuid4())
    started_at = datetime.utcnow().isoformat()

    def _noop() -> dict[str, str]:
        return {"ack": command_name}

    await broadcast_event(
        {"event": "ack", "command": command_name, "command_id": command_id}
    )

    try:
        result = _dispatcher.dispatch(operator, agent, _noop, command_id=command_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - dispatcher failure
        logger.error("dispatch failed: %s", exc)
        raise HTTPException(status_code=500, detail="dispatch failed") from exc

    completed_at = datetime.utcnow().isoformat()
    _log_command(
        {
            "command_id": command_id,
            "agent": agent,
            "result": result,
            "started_at": started_at,
            "completed_at": completed_at,
        }
    )

    await broadcast_event(
        {
            "event": "progress",
            "command": command_name,
            "percent": 100,
            "command_id": command_id,
        }
    )

    return {"command_id": command_id, "result": result}


@router.get("/operator/status")
async def operator_status() -> dict[str, object]:
    """Return component health, recent errors, and memory summary."""

    components: list[dict[str, object]] = []
    try:
        from razar import status_dashboard

        components = status_dashboard._component_statuses()  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - best effort
        components = []

    errors: list[str] = []
    log_path = Path("logs") / "razar_mission.log"
    if log_path.exists():
        lines = log_path.read_text().splitlines()[-20:]
        errors = [line for line in lines if "error" in line.lower()]

    mem_path = Path("memory")
    if mem_path.exists():
        files = [p for p in mem_path.rglob("*") if p.is_file()]
        mem_summary = {
            "files": len(files),
            "size_bytes": sum(p.stat().st_size for p in files),
        }
    else:
        mem_summary = {"files": 0, "size_bytes": 0}

    return {
        "components": components,
        "errors": errors,
        "memory": mem_summary,
    }


@router.get("/agents/interactions")
async def agent_interactions(
    agents: list[str] | None = None, limit: int = 100
) -> list[dict[str, object]]:
    """Return recent agent interactions filtered by ``agents``."""
    path = Path("logs") / "agent_interactions.jsonl"
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agents and not (
                entry.get("source") in agents or entry.get("target") in agents
            ):
                continue
            records.append(entry)
    return records[-limit:]


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
    command_id = str(uuid4())
    started_at = datetime.utcnow().isoformat()

    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid metadata") from exc

    upload_dir = Path("uploads") / operator
    upload_dir.mkdir(parents=True, exist_ok=True)

    await broadcast_event(
        {"event": "ack", "command": "upload", "command_id": command_id}
    )

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
                    "command_id": command_id,
                }
            )
        except Exception as exc:  # pragma: no cover - disk failure
            logger.error("failed to store %s: %s", item.filename, exc)
            raise HTTPException(status_code=500, detail="failed to store file") from exc

    def _relay(meta: dict[str, object]) -> dict[str, object]:
        """Crown forwards metadata and stored paths to RAZAR."""

        def _send(m: dict[str, object]) -> dict[str, object]:
            return {"received": m, "files": stored}

        return _dispatcher.dispatch(
            "crown", "razar", _send, meta, command_id=command_id
        )

    meta_with_files = {**meta, "files": stored, "command_id": command_id}

    try:
        _dispatcher.dispatch(
            operator, "crown", _relay, meta_with_files, command_id=command_id
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - dispatcher failure
        logger.error("metadata relay failed: %s", exc)
        raise HTTPException(status_code=500, detail="relay failed") from exc

    completed_at = datetime.utcnow().isoformat()
    _log_command(
        {
            "command_id": command_id,
            "agent": "crown",
            "result": {"stored": stored, "metadata": meta_with_files},
            "started_at": started_at,
            "completed_at": completed_at,
        }
    )

    await broadcast_event(
        {
            "event": "progress",
            "command": "upload",
            "percent": 100,
            "files": stored,
            "command_id": command_id,
        }
    )

    return {
        "command_id": command_id,
        "stored": stored,
        "metadata": meta_with_files,
    }


__all__ = ["router"]
