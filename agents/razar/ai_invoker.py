"""RAZAR AI handover invocation helper.

This module selects a remote agent based on a configuration file and
delegates failure contexts to it via
:func:`agents.razar.remote_loader.load_remote_agent`. Each invocation and
its resulting patch suggestion are appended to
``logs/razar_ai_invocations.json`` for audit purposes. Agents may require
dedicated HTTP endpoints and authentication tokens; both are supplied via
configuration and forwarded as part of the patch context. Consumers should
call :func:`handover` which returns either the patch suggestion from the
remote agent or a confirmation that no suggestion was provided.
"""

from __future__ import annotations

__version__ = "0.2.1"

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple, List

from . import remote_loader

logger = logging.getLogger(__name__)

# Default paths used by this module
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "razar_ai_agents.json"
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "razar_ai_invocations.json"

__all__ = ["handover"]


def _load_config(path: Path) -> Dict[str, Any]:
    """Return the parsed JSON configuration from ``path``.

    The configuration format is expected to be::

        {
            "active": "agent_name",            # optional
            "agents": [
                {
                    "name": "agent_name",
                    "endpoint": "http://...",
                    "auth": {"token": "..."}    # optional
                },
                ...
            ]
        }
    """
    if not path.exists():
        logger.error("Configuration file %s not found", path)
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Could not decode %s", path)
        return {}
    return data if isinstance(data, dict) else {}


def _select_agent(config: Dict[str, Any]) -> Tuple[str, str, str | None]:
    """Return ``(name, endpoint, token)`` for the active agent."""
    agents = config.get("agents")
    if not isinstance(agents, list) or not agents:
        raise RuntimeError("No agents configured")

    active = config.get("active")
    chosen = None
    if isinstance(active, str):
        for entry in agents:
            if entry.get("name") == active:
                chosen = entry
                break
    if chosen is None:
        chosen = agents[0]

    name = str(chosen.get("name"))
    endpoint = str(chosen.get("endpoint"))
    auth = chosen.get("auth", {})
    token = None
    if isinstance(auth, dict):
        token = str(auth.get("token") or auth.get("key") or "") or None
    return name, endpoint, token


def _append_log(entry: Dict[str, Any]) -> None:
    """Append ``entry`` to :data:`LOG_PATH`.

    ``entry`` should include an ``event`` field describing whether it represents
    an ``invocation`` or a ``patch_result``.
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []
    if LOG_PATH.exists():
        try:
            raw = LOG_PATH.read_text(encoding="utf-8")
            records = json.loads(raw)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            logger.warning("Could not decode %s; starting fresh", LOG_PATH)
    records.append(entry)
    LOG_PATH.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")


def handover(
    *, context: Any | None = None, config_path: Path | str | None = None
) -> Any:
    """Delegate ``context`` to a remote agent and return its suggestion.

    Parameters
    ----------
    context:
        Optional object describing the failure or state that triggered the
        handover.
    config_path:
        Optional override for the agent configuration file.  When omitted,
        :data:`CONFIG_PATH` is used.

    Returns
    -------
    Any
        The suggestion returned by the remote agent or ``{"handover": True}``
        when no suggestion is provided.
    """
    path = Path(config_path) if config_path is not None else CONFIG_PATH
    config = _load_config(path)
    name, endpoint, token = _select_agent(config)

    _append_log(
        {
            "event": "invocation",
            "name": name,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
        }
    )

    patch_context: Dict[str, Any] | None = None
    if context is not None or token is not None:
        patch_context = {}
        if isinstance(context, dict):
            patch_context.update(context)
        else:
            patch_context["context"] = context
        if token:
            patch_context["auth_token"] = token

    _module, agent_config, suggestion = remote_loader.load_remote_agent(
        name, endpoint, patch_context=patch_context
    )

    log_entry: Dict[str, Any] = {
        "event": "patch_result",
        "name": name,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if agent_config:
        log_entry["config"] = agent_config
    if suggestion is not None:
        log_entry["suggestion"] = suggestion
    _append_log(log_entry)

    return suggestion if suggestion is not None else {"handover": True}
