"""Operator command API exposing the :class:`OperatorDispatcher`."""

from __future__ import annotations

__version__ = "0.3.0"

import json
import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agents.operator_dispatcher import OperatorDispatcher

router = APIRouter()
_dispatcher = OperatorDispatcher(
    {
        "overlord": ["cocytus", "victim", "crown"],
        "auditor": ["victim"],
        "crown": ["razar"],
    }
)


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

    try:
        result = _dispatcher.dispatch(operator, agent, _noop)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"result": result}


@router.post("/operator/upload")
async def upload_file(
    operator: str = Form(...),
    metadata: str = Form("{}"),
    files: list[UploadFile] = File(...),
) -> dict[str, object]:
    """Store uploaded files and forward metadata to RAZAR via Crown."""
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid metadata") from exc

    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored: list[str] = []
    for item in files:
        dest = upload_dir / item.filename
        with dest.open("wb") as fh:
            shutil.copyfileobj(item.file, fh)
        stored.append(dest.name)

    def _relay(meta: dict[str, object]) -> dict[str, object]:
        """Crown forwards metadata to RAZAR."""

        def _send(m: dict[str, object]) -> dict[str, object]:
            return {"received": m}

        return _dispatcher.dispatch("crown", "razar", _send, meta)

    try:
        _dispatcher.dispatch(operator, "crown", _relay, meta)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return {"stored": stored, "metadata": meta}


__all__ = ["router"]
