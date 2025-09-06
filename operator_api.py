"""Operator command API exposing the :class:`OperatorDispatcher`.

- **Endpoints:** ``POST /operator/command``, ``POST /operator/upload``
- **Auth:** Bearer token
- **Linked agents:** Orchestration Master via Crown, RAZAR
"""

from __future__ import annotations

__version__ = "0.3.6"

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
from agents.interaction_log import log_agent_interaction
from fastapi.responses import HTMLResponse
from servant_model_manager import (
    has_model,
    list_models,
    register_kimi_k2,
    register_opencode,
    register_subprocess_model,
    unregister_model,
)
from typing import cast

from scripts.ingest_ethics import ingest_ethics as run_ingest_ethics

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
_chat_rooms: dict[str, set[WebSocket]] = {}


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


@router.websocket("/agent/chat/{agents}")
async def agent_chat(websocket: WebSocket, agents: str) -> None:
    """WebSocket room forwarding messages between ``agents``.

    The ``agents`` path parameter uses ``<agentA>-<agentB>``. Any JSON message
    received is broadcast to all peers in the room and recorded via
    :func:`log_agent_interaction`.
    """

    await websocket.accept()
    clients = _chat_rooms.setdefault(agents, set())
    clients.add(websocket)
    parts = agents.split("-", 1)
    agent_a = parts[0] if parts else ""
    agent_b = parts[1] if len(parts) > 1 else ""
    try:
        while True:
            message = await websocket.receive_text()
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue
            sender = data.get("sender", "")
            text = data.get("text", "")
            target = data.get("target") or (agent_b if sender == agent_a else agent_a)
            log_agent_interaction(
                {"source": sender, "target": target, "text": text, "room": agents}
            )
            payload = {
                "sender": sender,
                "target": target,
                "text": text,
                "timestamp": datetime.utcnow().isoformat(),
            }
            for ws in set(clients):
                try:
                    await ws.send_text(json.dumps(payload))
                except Exception:
                    clients.discard(ws)
    except WebSocketDisconnect:
        clients.discard(websocket)
    finally:
        if not clients:
            _chat_rooms.pop(agents, None)


@router.get("/chat/{agents}")
async def chat_page(agents: str) -> HTMLResponse:  # pragma: no cover - simple
    """Return the static chat console page."""

    path = Path("web_console") / "chat.html"
    return HTMLResponse(path.read_text(encoding="utf-8"))


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

        components = cast(
            list[dict[str, object]],
            status_dashboard._component_statuses(),  # type: ignore[attr-defined]
        )
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


@router.post("/operator/models")
async def register_servant_model(data: dict[str, object]) -> dict[str, list[str]]:
    """Register a servant model at runtime."""

    name = str(data.get("name", ""))
    builtin = data.get("builtin")
    command = data.get("command")
    replace = bool(data.get("replace", False))

    if not name:
        raise HTTPException(status_code=400, detail="name required")
    if has_model(name) and not replace:
        raise HTTPException(status_code=409, detail="model exists")
    if builtin == "kimi_k2":
        register_kimi_k2()
    elif builtin == "opencode":
        register_opencode()
    elif isinstance(command, list):
        if replace and has_model(name):
            unregister_model(name)
        register_subprocess_model(name, [str(c) for c in command])
    else:
        raise HTTPException(status_code=400, detail="builtin or command required")
    return {"models": list_models()}


@router.delete("/operator/models/{name}")
async def unregister_servant_model(name: str) -> dict[str, list[str]]:
    """Unregister a servant model at runtime."""

    if not has_model(name):
        raise HTTPException(status_code=404, detail="unknown model")
    unregister_model(name)
    return {"models": list_models()}


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


@router.get("/conversation/logs")
async def conversation_logs(
    agent: str | None = None, limit: int = 100
) -> dict[str, object]:
    """Return logged conversation entries for ``agent``."""

    agents = [agent] if agent else None
    logs = await agent_interactions(agents, limit)
    return {"logs": logs}


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


@router.post("/ingest-ethics")
async def ingest_ethics_endpoint(directory: str | None = None) -> dict[str, object]:
    """Reindex the ethics corpus and update Chroma memory."""
    target_dir = Path(directory) if directory else Path("sacred_inputs")
    if not run_ingest_ethics(target_dir):
        raise HTTPException(status_code=500, detail="ingestion failed")
    return {"status": "ok", "directory": str(target_dir)}


__all__ = ["router"]
