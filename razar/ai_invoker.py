"""High level wrapper for remote RAZAR agents.

This module delegates failure contexts to the configured remote agent and
applies any suggested patches via :mod:`agents.razar.code_repair`.
"""

from __future__ import annotations

__all__ = ["handover", "load_agent_definitions"]

import json
import logging
import os
import subprocess
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .bootstrap_utils import PATCH_LOG_PATH, LOGS_DIR
from . import health_checks
from tools import opencode_client

__version__ = "0.1.4"

LOGGER = logging.getLogger(__name__)

PATCH_BACKUP_DIR = LOGS_DIR / "patch_backups"
AGENT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "razar_ai_agents.json"
)


@dataclass(frozen=True)
class AgentDefinition:
    """Normalized representation of a remote agent entry."""

    name: str
    normalized: str
    endpoint: str | None
    token: str | None
    raw: Dict[str, Any]


def _expand_env(value: Any) -> str | None:
    """Return ``value`` with environment variables expanded."""

    if not isinstance(value, str):
        return None
    expanded = os.path.expandvars(value).strip()
    if not expanded or ("${" in expanded and "}" in expanded):
        return None
    return expanded


def _load_agent_config(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_agent_definitions(
    path: Path = AGENT_CONFIG_PATH,
) -> tuple[str | None, list[AgentDefinition]]:
    """Return the active agent and roster parsed from ``path``."""

    config = _load_agent_config(path)
    raw_active = config.get("active")
    active = raw_active.lower() if isinstance(raw_active, str) else None

    definitions: list[AgentDefinition] = []
    agents = config.get("agents")
    if isinstance(agents, list):
        for entry in agents:
            if isinstance(entry, dict):
                payload = dict(entry)
                name = payload.get("name")
            elif isinstance(entry, str):
                payload = {"name": entry}
                name = entry
            else:
                continue
            if not isinstance(name, str):
                continue
            endpoint = _expand_env(payload.get("endpoint"))
            token: str | None = None
            auth = payload.get("auth")
            if isinstance(auth, dict):
                token = _expand_env(auth.get("token") or auth.get("key"))
            definitions.append(
                AgentDefinition(
                    name=name,
                    normalized=name.lower(),
                    endpoint=endpoint,
                    token=token,
                    raw=payload,
                )
            )

    if active is None and definitions:
        active = definitions[0].normalized

    return active, definitions


def _active_agent(path: Path = AGENT_CONFIG_PATH) -> str | None:
    """Return the normalized name of the active remote agent."""

    active, _definitions = load_agent_definitions(path)
    return active


def _append_patch_log(entry: Dict[str, Any]) -> None:
    """Append ``entry`` to :data:`PATCH_LOG_PATH`."""
    PATCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    records: list[Dict[str, Any]] = []
    if PATCH_LOG_PATH.exists():
        try:
            records = json.loads(PATCH_LOG_PATH.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                records = []
        except json.JSONDecodeError:
            records = []
    records.append(entry)
    PATCH_LOG_PATH.write_text(
        json.dumps(records, indent=2, sort_keys=True), encoding="utf-8"
    )


def _diff_to_suggestions(diff: str, error: str) -> list[Dict[str, Any]]:
    """Return patch suggestions parsed from ``diff``.

    Each ``+++`` line denotes the target module path. ``/dev/null`` entries
    are ignored. The resulting suggestions mirror the structure produced by
    the ``opencode run --json`` command so that they can be processed by the
    existing patch-application flow.
    """

    suggestions: list[Dict[str, Any]] = []
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            if path and path != "/dev/null":
                suggestions.append({"module": path, "error": error, "tests": []})
    return suggestions


def handover(
    component: str,
    error: str,
    *,
    context: Dict[str, Any] | None = None,
    config_path: Path | str | None = None,
    use_opencode: bool | None = None,
) -> bool:
    """Delegate ``component`` failure to a remote agent or the ``opencode`` CLI.

    Parameters
    ----------
    component:
        Name of the failing component.
    error:
        Error message describing the failure.
    context:
        Optional additional context forwarded to the remote agent.
    config_path:
        Optional override for the remote agent configuration file.
    use_opencode:
        When ``True`` invoke ``opencode run --json`` with the failure context
        instead of delegating to a remote agent.

    Returns
    -------
    bool
        ``True`` if at least one patch was applied successfully, otherwise
        ``False``.
    """
    from agents.razar import ai_invoker as remote_ai_invoker
    from agents.razar import code_repair

    ctx: Dict[str, Any] = {"component": component, "error": error}
    if context:
        history = context.get("history")
        if history:
            existing = ctx.setdefault("history", [])
            existing.extend(history)
        ctx.update({k: v for k, v in context.items() if k != "history"})
    suggestion: Any | None = None
    if use_opencode is None:
        active = _active_agent(Path(config_path) if config_path else AGENT_CONFIG_PATH)
        use_opencode = active not in {"kimi2", "airstar", "rstar"}
    if use_opencode:
        try:
            result = subprocess.run(
                ["opencode", "run", "--json"],
                input=json.dumps(ctx),
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            LOGGER.info("opencode CLI not found; falling back to library")
            try:
                diff = opencode_client.complete(json.dumps(ctx))
            except Exception:  # pragma: no cover - defensive
                LOGGER.exception("opencode client failed for %s", component)
                return False
            suggestion = _diff_to_suggestions(diff, error)
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("opencode CLI failed for %s", component)
            return False
        else:
            if result.returncode != 0:
                LOGGER.error(
                    "opencode exited with code %s; using library fallback",
                    result.returncode,
                )
                try:
                    diff = opencode_client.complete(json.dumps(ctx))
                except Exception:  # pragma: no cover - defensive
                    LOGGER.exception("opencode client failed for %s", component)
                    return False
                suggestion = _diff_to_suggestions(diff, error)
            else:
                try:
                    suggestion = json.loads(result.stdout or "null")
                except json.JSONDecodeError:
                    LOGGER.warning("Could not decode opencode output for %s", component)
                    return False
    else:
        try:
            suggestion = remote_ai_invoker.handover(
                context=ctx, config_path=config_path
            )
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Remote agent invocation failed for %s", component)
            return False
    if not suggestion:
        return False
    patches = suggestion if isinstance(suggestion, list) else [suggestion]
    applied = False
    for patch in patches:
        module = patch.get("module")
        if not module:
            continue
        module_path = Path(module)
        tests = [Path(p) for p in patch.get("tests", [])]
        err = patch.get("error", error)
        backup_path: Path | None = None
        try:
            PATCH_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
            backup_path = PATCH_BACKUP_DIR / f"{module_path.name}.{ts}"
            if module_path.exists():
                shutil.copy2(module_path, backup_path)
            else:
                backup_path = None
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed to snapshot %s", module)
            backup_path = None
        for attempt in range(1, 3):
            try:
                success = code_repair.repair_module(module_path, tests, err)
            except Exception:  # pragma: no cover - defensive
                LOGGER.exception("Failed to apply patch for %s", module)
                success = False
            if success:
                try:
                    if not health_checks.run(component):
                        if backup_path and backup_path.exists():
                            shutil.copy2(backup_path, module_path)
                        success = False
                except Exception:  # pragma: no cover - defensive
                    LOGGER.exception("Post-restart check failed for %s", component)
                    if backup_path and backup_path.exists():
                        shutil.copy2(backup_path, module_path)
                    success = False
            _append_patch_log(
                {
                    "event": "patch_attempt",
                    "component": component,
                    "module": module,
                    "attempt": attempt,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            if success:
                applied = True
                break
    return applied
