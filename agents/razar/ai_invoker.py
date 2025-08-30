"""High level wrapper for remote RAZAR agents.

This module selects a remote agent based on a configuration file and delegates
loading to :func:`agents.razar.remote_loader.load_remote_agent`.  Each
invocation and its resulting patch suggestion are appended to
``logs/razar_ai_invocations.json`` for audit purposes.  Consumers should call
:func:`handover` which returns either the patch suggestion from the remote agent
or a confirmation that no suggestion was provided.
"""

from __future__ import annotations

__version__ = "0.1.0"

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
                {"name": "agent_name", "url": "http://..."},
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


def _select_agent(config: Dict[str, Any]) -> Tuple[str, str]:
    """Return ``(name, url)`` for the active agent in ``config``."""
    agents = config.get("agents")
    if not isinstance(agents, list) or not agents:
        raise RuntimeError("No agents configured")

    active = config.get("active")
    if isinstance(active, str):
        for entry in agents:
            if entry.get("name") == active:
                return str(entry.get("name")), str(entry.get("url"))

    # Fall back to the first configured agent
    entry = agents[0]
    return str(entry.get("name")), str(entry.get("url"))


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
    *, config_path: Path | str | None = None, patch_context: Any | None = None
) -> Any:
    """Invoke the configured remote agent and return its patch suggestion.

    Parameters
    ----------
    config_path:
        Optional override for the agent configuration file.  When omitted,
        :data:`CONFIG_PATH` is used.
    patch_context:
        Optional object passed to the agent's ``patch()`` function.

    Returns
    -------
    Any
        The suggestion returned by the remote agent or ``{"handover": True}``
        when no suggestion is provided.
    """
    path = Path(config_path) if config_path is not None else CONFIG_PATH
    config = _load_config(path)
    name, url = _select_agent(config)

    _append_log(
        {
            "event": "invocation",
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    _module, agent_config, suggestion = remote_loader.load_remote_agent(
        name, url, patch_context=patch_context
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
