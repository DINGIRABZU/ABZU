"""Operator command API exposing the :class:`OperatorDispatcher`.

- **Endpoints:** ``POST /operator/command``, ``POST /operator/upload``
- **Auth:** Bearer token
- **Linked agents:** Orchestration Master via Crown, RAZAR
"""

from __future__ import annotations

__version__ = "0.3.7"

import asyncio
import contextlib
import json
import logging
import shutil
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from typing import Any, Mapping

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
from bana import narrative as bana_narrative
from agents.task_orchestrator import run_mission
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

from memory import query_memory
from razar import ai_invoker, boot_orchestrator
from scripts.ingest_ethics import ingest_ethics as run_ingest_ethics
from connectors.operator_mcp_adapter import (
    OperatorMCPAdapter,
    record_rotation_drill,
    stage_b_context_enabled,
)

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

_MCP_ADAPTER: OperatorMCPAdapter | None = None
_MCP_SESSION: Mapping[str, Any] | None = None
_MCP_HEARTBEAT_TASK: asyncio.Task[None] | None = None
_MCP_LOCK: asyncio.Lock | None = None
_LAST_CREDENTIAL_EXPIRY: datetime | None = None

_STAGE_A_ROOT = Path("logs") / "stage_a"


async def _ensure_lock() -> asyncio.Lock:
    global _MCP_LOCK
    if _MCP_LOCK is None:
        _MCP_LOCK = asyncio.Lock()
    return _MCP_LOCK


def _normalize_credential_expiry(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            logger.warning("invalid credential_expiry value: %s", value)
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _process_handshake(handshake: Mapping[str, Any]) -> None:
    global _MCP_SESSION, _LAST_CREDENTIAL_EXPIRY

    session = handshake.get("session")
    if isinstance(session, Mapping):
        _MCP_SESSION = session
        expiry = _normalize_credential_expiry(session.get("credential_expiry"))
        if expiry and (
            _LAST_CREDENTIAL_EXPIRY is None or expiry != _LAST_CREDENTIAL_EXPIRY
        ):
            _LAST_CREDENTIAL_EXPIRY = expiry
            for connector_id in ("operator_api", "operator_upload"):
                record_rotation_drill(connector_id, rotated_at=expiry)
    else:
        _MCP_SESSION = None


async def _heartbeat_loop(adapter: OperatorMCPAdapter) -> None:
    interval = getattr(adapter, "_interval", 30.0)
    while True:
        try:
            payload = {
                "event": "stage-b-heartbeat",
                "service": "operator_api",
                "timestamp": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
            }
            await adapter.emit_stage_b_heartbeat(
                payload, credential_expiry=_LAST_CREDENTIAL_EXPIRY
            )
        except asyncio.CancelledError:  # pragma: no cover - shutdown path
            raise
        except Exception:  # pragma: no cover - best effort telemetry
            logger.exception("operator MCP heartbeat failed")
        await asyncio.sleep(float(interval))


def _start_heartbeat_task(adapter: OperatorMCPAdapter) -> None:
    global _MCP_HEARTBEAT_TASK
    if _MCP_HEARTBEAT_TASK is not None and not _MCP_HEARTBEAT_TASK.done():
        return
    loop = asyncio.get_running_loop()
    _MCP_HEARTBEAT_TASK = loop.create_task(_heartbeat_loop(adapter))


async def _init_mcp_adapter() -> None:
    global _MCP_ADAPTER

    if not stage_b_context_enabled():
        return

    lock = await _ensure_lock()
    async with lock:
        adapter = _MCP_ADAPTER
        created = False
        if adapter is None:
            adapter = OperatorMCPAdapter()
            _MCP_ADAPTER = adapter
            created = True

        if adapter is None:  # pragma: no cover - defensive
            return

        handshake = await adapter.ensure_handshake()
        _process_handshake(handshake)

        if created:
            adapter.start()

        if _MCP_HEARTBEAT_TASK is None or _MCP_HEARTBEAT_TASK.done():
            _start_heartbeat_task(adapter)


async def _ensure_mcp_ready_for_request() -> None:
    try:
        await _init_mcp_adapter()
    except Exception as exc:  # pragma: no cover - handshake failure
        logger.exception("operator MCP handshake failed: %s", exc)
        raise HTTPException(
            status_code=503, detail="operator MCP handshake failed"
        ) from exc


async def _run_stage_a_workflow(slug: str, command: list[str]) -> dict[str, Any]:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slug}"
    log_dir = _STAGE_A_ROOT / run_id
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_path = log_dir / f"{slug}.stdout.log"
    stderr_path = log_dir / f"{slug}.stderr.log"
    summary_path = log_dir / "summary.json"

    started_at = datetime.now(timezone.utc)

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        completed_at = datetime.now(timezone.utc)
        stderr_text = f"failed to spawn command: {exc}"
        stdout_path.write_bytes(b"")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        payload: dict[str, Any] = {
            "status": "error",
            "stage": slug,
            "run_id": run_id,
            "command": command,
            "returncode": None,
            "error": stderr_text,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": (completed_at - started_at).total_seconds(),
            "log_dir": str(log_dir),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "stdout_lines": 0,
            "stderr_lines": len(stderr_text.splitlines()),
            "stderr_tail": stderr_text.splitlines()[-10:],
        }
        summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["summary_path"] = str(summary_path)
        return payload

    stdout_bytes, stderr_bytes = await process.communicate()
    completed_at = datetime.now(timezone.utc)

    stdout_path.write_bytes(stdout_bytes)
    stderr_path.write_bytes(stderr_bytes)

    stdout_text = stdout_bytes.decode("utf-8", errors="replace")
    stderr_text = stderr_bytes.decode("utf-8", errors="replace")
    stdout_lines = stdout_text.splitlines()
    stderr_lines = stderr_text.splitlines()

    summary_line = next((line for line in reversed(stdout_lines) if line.strip()), "")

    payload = {
        "status": "success" if process.returncode == 0 else "error",
        "stage": slug,
        "run_id": run_id,
        "command": command,
        "returncode": process.returncode,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_seconds": (completed_at - started_at).total_seconds(),
        "log_dir": str(log_dir),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_lines": len(stdout_lines),
        "stderr_lines": len(stderr_lines),
        "stderr_tail": stderr_lines[-10:],
    }
    if summary_line:
        payload["summary"] = summary_line
    if stderr_text.strip():
        payload["stderr"] = stderr_text
    if payload["status"] == "error":
        payload.setdefault("error", f"{slug} exited with code {process.returncode}")

    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["summary_path"] = str(summary_path)
    return payload


@router.on_event("startup")
async def _operator_mcp_startup() -> None:
    try:
        await _init_mcp_adapter()
    except Exception:  # pragma: no cover - startup best effort
        logger.exception("operator MCP adapter startup failed")


@router.on_event("shutdown")
async def _operator_mcp_shutdown() -> None:
    global _MCP_ADAPTER, _MCP_HEARTBEAT_TASK, _MCP_SESSION, _LAST_CREDENTIAL_EXPIRY

    if _MCP_HEARTBEAT_TASK is not None:
        _MCP_HEARTBEAT_TASK.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _MCP_HEARTBEAT_TASK
        _MCP_HEARTBEAT_TASK = None

    if _MCP_ADAPTER is not None:
        try:
            _MCP_ADAPTER.stop()
        except Exception:  # pragma: no cover - defensive cleanup
            logger.exception("operator MCP adapter shutdown failed")
        _MCP_ADAPTER = None

    _MCP_SESSION = None
    _LAST_CREDENTIAL_EXPIRY = None


def _log_command(entry: dict[str, object]) -> None:
    """Append ``entry`` to ``logs/operator_commands.jsonl``."""
    path = Path("logs") / "operator_commands.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=repr) + "\n")
    try:
        bana_narrative.emit("operator", "decision", entry, target_agent="bana")
    except Exception:  # pragma: no cover - narrative errors
        logger.exception("failed to emit operator decision")


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
    await _ensure_mcp_ready_for_request()
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


@router.post("/start_ignition")
async def start_ignition() -> dict[str, str]:
    """Kick off ignition via ``boot_orchestrator.start``."""

    boot_orchestrator.start()  # type: ignore[attr-defined]
    return {"status": "started"}


@router.post("/memory/query")
async def memory_query_endpoint(payload: dict[str, str]) -> dict[str, object]:
    """Return aggregated memory search results via :func:`query_memory`."""

    query = payload.get("query", "")
    return {"results": query_memory(query)}


@router.post("/handover")
async def handover_endpoint(payload: dict[str, str] | None = None) -> dict[str, object]:
    """Escalate failure context to AI handover."""

    data = payload or {}
    component = data.get("component", "unknown")
    error = data.get("error", "operator initiated")
    result = ai_invoker.handover(component, error)
    return {"handover": result}


@router.post("/alpha/stage-a1-boot-telemetry")
async def stage_a1_boot_telemetry() -> dict[str, Any]:
    """Execute the bootstrap telemetry sweep and archive logs under ``logs/stage_a``."""

    command = [sys.executable, "scripts/bootstrap.py"]
    return await _run_stage_a_workflow("stage_a1_boot_telemetry", command)


@router.post("/alpha/stage-a2-crown-replays")
async def stage_a2_crown_replays() -> dict[str, Any]:
    """Capture Crown replay evidence for Stage A auditing."""

    command = [sys.executable, "scripts/crown_capture_replays.py"]
    return await _run_stage_a_workflow("stage_a2_crown_replays", command)


@router.post("/alpha/stage-a3-gate-shakeout")
async def stage_a3_gate_shakeout() -> dict[str, Any]:
    """Run the Alpha gate automation shakeout script."""

    command = ["bash", "scripts/run_alpha_gate.sh"]
    return await _run_stage_a_workflow("stage_a3_gate_shakeout", command)


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
    await _ensure_mcp_ready_for_request()
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


@router.post("/missions")
async def save_and_run_mission(payload: dict[str, object]) -> dict[str, str]:
    """Persist ``payload['mission']`` under ``missions/`` and dispatch it."""

    name = str(payload.get("name") or f"mission_{uuid4().hex}")
    events = payload.get("mission", [])
    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="mission must be a list")
    path = Path("missions") / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(events, indent=2), encoding="utf-8")
    run_mission(events)
    return {"status": "ok", "path": str(path)}


__all__ = ["router"]
