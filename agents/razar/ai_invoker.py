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

__version__ = "0.2.5"

from datetime import datetime
import os
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Tuple, List

import requests

from . import remote_loader, code_repair

logger = logging.getLogger(__name__)

# Default paths used by this module
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "razar_ai_agents.json"
INVOCATION_LOG_PATH = (
    Path(__file__).resolve().parents[2] / "logs" / "razar_ai_invocations.json"
)
PATCH_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "razar_ai_patches.json"

__all__ = ["handover"]


class AgentCredentialError(RuntimeError):
    """Raised when a remote agent credential is missing or invalid."""


_MANDATORY_AGENT_ENV_VARS: Dict[str, str] = {
    "kimi2": "KIMI2_API_KEY",
    "airstar": "AIRSTAR_API_KEY",
    "rstar": "RSTAR_API_KEY",
}

_AGENT_SECRET_ENV_HINTS: Dict[str, Tuple[str, ...]] = {
    name: (env_var,) for name, env_var in _MANDATORY_AGENT_ENV_VARS.items()
}


def _expand_env(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    expanded = os.path.expandvars(value).strip()
    if not expanded or ("${" in expanded and "}" in expanded):
        return None
    return expanded


def _normalize_agent_entry(entry: Any) -> Dict[str, Any] | None:
    if isinstance(entry, dict):
        return dict(entry)
    if isinstance(entry, str):
        return {"name": entry}
    return None


def _sanitize_env_key(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name).upper()


def _candidate_secret_keys(name: str) -> Tuple[str, ...]:
    normalized = name.lower()
    required = _MANDATORY_AGENT_ENV_VARS.get(normalized)
    if required:
        return (required,)
    hints = _AGENT_SECRET_ENV_HINTS.get(normalized)
    if hints:
        return hints
    base = _sanitize_env_key(name)
    return (f"{base}_API_KEY", f"{base}_TOKEN")


def _require_env_secret(agent: str, env_key: str) -> str:
    raw_value = os.environ.get(env_key)
    if raw_value is None:
        message = f"Environment variable {env_key} is required for agent {agent}"
        logger.error(message)
        raise AgentCredentialError(message)
    token = raw_value.strip()
    if not token:
        message = f"Environment variable {env_key} for agent {agent} must not be empty"
        logger.error(message)
        raise AgentCredentialError(message)
    return token


def _agent_env_token(name: str) -> str | None:
    normalized = name.lower()
    required_env = _MANDATORY_AGENT_ENV_VARS.get(normalized)
    if required_env:
        return _require_env_secret(name, required_env)

    for key in _candidate_secret_keys(name):
        value = os.environ.get(key)
        if value is None:
            continue
        token = value.strip()
        if token:
            return token
        logger.error(
            "Environment variable %s for agent %s is defined but empty",
            key,
            name,
        )
    return None


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


def _select_agent(config: Dict[str, Any]) -> Tuple[str, str | None, str | None]:
    """Return ``(name, endpoint, token)`` for the active agent."""

    agents = config.get("agents")
    if not isinstance(agents, list) or not agents:
        raise RuntimeError("No agents configured")

    normalized_agents: list[Dict[str, Any]] = []
    for entry in agents:
        payload = _normalize_agent_entry(entry)
        if payload is not None:
            normalized_agents.append(payload)

    if not normalized_agents:
        raise RuntimeError("No agents configured")

    active = config.get("active")
    active_name = active.lower() if isinstance(active, str) else None

    chosen = None
    for entry in normalized_agents:
        candidate = entry.get("name")
        if (
            isinstance(candidate, str)
            and active_name
            and candidate.lower() == active_name
        ):
            chosen = entry
            break

    if chosen is None:
        chosen = normalized_agents[0]

    name = chosen.get("name")
    if not isinstance(name, str):
        raise RuntimeError("Agent entry missing name")

    endpoint = _expand_env(chosen.get("endpoint"))
    token: str | None = None
    auth = chosen.get("auth", {})
    if isinstance(auth, dict):
        config_token = _expand_env(auth.get("token") or auth.get("key"))
        if isinstance(config_token, str):
            stripped = config_token.strip()
            if stripped:
                token = stripped

    env_token = _agent_env_token(name)
    if env_token:
        token = env_token

    return name, endpoint, token


def _append_log(path: Path, entry: Dict[str, Any]) -> None:
    """Append ``entry`` to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []
    if path.exists():
        try:
            raw = path.read_text(encoding="utf-8")
            records = json.loads(raw)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            logger.warning("Could not decode %s; starting fresh", path)
    records.append(entry)
    path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")


def _prepare_payload(context: Any | None) -> Dict[str, Any]:
    if isinstance(context, dict):
        return dict(context)
    if context is None:
        return {}
    return {"context": context}


def _call_patch_service(
    name: str,
    endpoint: str | None,
    patch_context: Any | None,
    token: str | None,
    *,
    timeout: float = 60.0,
) -> tuple[SimpleNamespace, Dict[str, Any], Any]:
    if not endpoint:
        raise RuntimeError(f"Agent {name} is missing an endpoint")

    payload = _prepare_payload(patch_context)
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-API-Key"] = token
        if isinstance(payload, dict) and "auth_token" not in payload:
            payload["auth_token"] = token

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers or None,
            timeout=timeout,
        )
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("Request for %s failed: %s", name, exc)
        raise

    try:
        suggestion = response.json()
    except ValueError:
        suggestion = {"response": response.text}

    agent_config: Dict[str, Any] = {
        "endpoint": endpoint,
        "service": name.lower(),
        "status_code": getattr(response, "status_code", None),
    }
    if token:
        agent_config["token_provided"] = True

    return SimpleNamespace(__name__=name), agent_config, suggestion


# Adapter for the MoonshotAI Kimi-K2 service: https://github.com/MoonshotAI/Kimi-K2
def _invoke_kimi2(
    name: str,
    endpoint: str | None,
    patch_context: Any | None,
    token: str | None,
) -> tuple[SimpleNamespace, Dict[str, Any], Any]:
    return _call_patch_service(name, endpoint, patch_context, token)


def _invoke_airstar(
    name: str,
    endpoint: str | None,
    patch_context: Any | None,
    token: str | None,
) -> tuple[SimpleNamespace, Dict[str, Any], Any]:
    return _call_patch_service(name, endpoint, patch_context, token)


# Adapter for the Microsoft rStar patch service: https://github.com/microsoft/rStar
def _invoke_rstar(
    name: str,
    endpoint: str | None,
    patch_context: Any | None,
    token: str | None,
) -> tuple[SimpleNamespace, Dict[str, Any], Any]:
    return _call_patch_service(name, endpoint, patch_context, token)


def _dispatch_agent(
    name: str,
    endpoint: str | None,
    token: str | None,
    patch_context: Dict[str, Any] | None,
) -> tuple[SimpleNamespace, Dict[str, Any], Any]:
    normalized = name.lower()
    if normalized == "kimi2":
        return _invoke_kimi2(name, endpoint, patch_context, token)
    if normalized == "airstar":
        return _invoke_airstar(name, endpoint, patch_context, token)
    if normalized == "rstar":
        return _invoke_rstar(name, endpoint, patch_context, token)
    if not endpoint:
        raise RuntimeError(f"Agent {name} is missing an endpoint")
    return remote_loader.load_remote_agent(name, endpoint, patch_context=patch_context)


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
        INVOCATION_LOG_PATH,
        {
            "event": "invocation",
            "name": name,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
        },
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

    _module, agent_config, suggestion = _dispatch_agent(
        name, endpoint, token, patch_context
    )

    applied: bool | None = None
    if isinstance(suggestion, dict):
        module_path = suggestion.get("module")
        tests = suggestion.get("tests")
        error = suggestion.get("error", "")
        if module_path and tests:
            try:
                test_paths = [
                    Path(p) for p in (tests if isinstance(tests, list) else [tests])
                ]
                applied = code_repair.repair_module(
                    Path(module_path), test_paths, error
                )
            except Exception as exc:  # pragma: no cover - runtime safeguard
                logger.error("code_repair failed: %s", exc)

    log_entry: Dict[str, Any] = {
        "event": "suggestion" if suggestion is not None else "no_suggestion",
        "name": name,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if agent_config:
        log_entry["config"] = agent_config
    if suggestion is not None:
        log_entry["suggestion"] = suggestion
    if applied is not None:
        log_entry["applied"] = applied
    _append_log(PATCH_LOG_PATH, log_entry)

    return suggestion if suggestion is not None else {"handover": True}
