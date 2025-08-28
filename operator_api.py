from __future__ import annotations

"""Operator command API exposing the :class:`OperatorDispatcher`."""

from fastapi import APIRouter, HTTPException

from agents.operator_dispatcher import OperatorDispatcher

router = APIRouter()
_dispatcher = OperatorDispatcher({"overlord": ["cocytus", "victim"], "auditor": ["victim"]})


@router.post("/operator/command")
async def dispatch_command(data: dict[str, str]) -> dict[str, object]:
    """Dispatch an operator command to a target agent."""
    operator = data.get("operator", "")
    agent = data.get("agent", "")
    command_name = data.get("command", "")
    if not operator or not agent or not command_name:
        raise HTTPException(status_code=400, detail="operator, agent and command required")

    def _noop() -> dict[str, str]:
        return {"ack": command_name}

    try:
        result = _dispatcher.dispatch(operator, agent, _noop)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"result": result}


__all__ = ["router"]
