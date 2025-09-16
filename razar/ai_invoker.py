"""High level wrapper for remote RAZAR agents.

This module delegates failure contexts to the configured remote agent and
applies any suggested patches via :mod:`agents.razar.code_repair`.
"""

from __future__ import annotations

__all__ = ["handover", "load_agent_definitions", "invalidate_agent_config_cache"]

import json
import logging
import multiprocessing
import os
import queue
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict

from . import health_checks, metrics
from .bootstrap_utils import PATCH_LOG_PATH, LOGS_DIR
from tools import opencode_client

__version__ = "0.1.4"

LOGGER = logging.getLogger(__name__)

PATCH_BACKUP_DIR = LOGS_DIR / "patch_backups"
AGENT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "razar_ai_agents.json"
)

try:  # pragma: no cover - platform specific
    import resource
except ImportError:  # pragma: no cover - platform specific
    resource = None  # type: ignore[assignment]


_AGENT_SECRET_ENV_HINTS: Dict[str, tuple[str, ...]] = {
    "kimi2": ("KIMI2_API_KEY", "KIMI2_TOKEN"),
    "airstar": (
        "AIRSTAR_API_KEY",
        "AIRSTAR_TOKEN",
        "RSTAR_API_KEY",
        "RSTAR_TOKEN",
    ),
    "rstar": (
        "RSTAR_API_KEY",
        "RSTAR_TOKEN",
        "AIRSTAR_API_KEY",
        "AIRSTAR_TOKEN",
    ),
}

_CONFIG_CACHE: dict[Path, tuple[float, Dict[str, Any]]] = {}
_CONFIG_CACHE_LOCK = RLock()

_SANDBOX_TIMEOUT_SECONDS = 90.0
_SANDBOX_MEMORY_LIMIT_MB = 512


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


def _normalize_config_path(path: Path | str | None) -> Path:
    candidate = AGENT_CONFIG_PATH if path is None else path
    if not isinstance(candidate, Path):
        candidate = Path(candidate)
    candidate = candidate.expanduser()
    try:
        return candidate.resolve(strict=False)
    except RuntimeError:  # pragma: no cover - pathological symlink loops
        return candidate


def invalidate_agent_config_cache(path: Path | str | None = None) -> None:
    """Remove cached agent configuration data."""

    if path is None:
        with _CONFIG_CACHE_LOCK:
            _CONFIG_CACHE.clear()
        return

    normalized = _normalize_config_path(path)
    with _CONFIG_CACHE_LOCK:
        _CONFIG_CACHE.pop(normalized, None)


def _load_agent_config(path: Path | str) -> Dict[str, Any]:
    normalized = _normalize_config_path(path)
    try:
        mtime = normalized.stat().st_mtime
    except OSError:
        invalidate_agent_config_cache(normalized)
        return {}

    with _CONFIG_CACHE_LOCK:
        cached = _CONFIG_CACHE.get(normalized)
        if cached and cached[0] == mtime:
            return dict(cached[1])

    try:
        data = json.loads(normalized.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}

    snapshot = dict(data)
    with _CONFIG_CACHE_LOCK:
        _CONFIG_CACHE[normalized] = (mtime, snapshot)
    return dict(snapshot)


def _sanitize_env_key(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name).upper()


def _candidate_secret_keys(name: str) -> tuple[str, ...]:
    normalized = name.lower()
    hints = _AGENT_SECRET_ENV_HINTS.get(normalized)
    if hints:
        return hints
    base = _sanitize_env_key(name)
    return (f"{base}_API_KEY", f"{base}_TOKEN")


def _agent_env_token(name: str) -> str | None:
    for key in _candidate_secret_keys(name):
        value = os.environ.get(key)
        if value:
            token = value.strip()
            if token:
                return token
    return None


def load_agent_definitions(
    path: Path | str = AGENT_CONFIG_PATH,
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
            env_token = _agent_env_token(name)
            if env_token:
                token = env_token
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


def _active_agent(path: Path | str = AGENT_CONFIG_PATH) -> str | None:
    """Return the normalized name of the active remote agent."""

    active, _definitions = load_agent_definitions(path)
    if isinstance(active, str):
        return active.lower()
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


def _remote_agent_worker(
    queue_out: multiprocessing.Queue,
    ctx: Dict[str, Any] | None,
    config_path: Path | str | None,
    memory_limit_mb: int,
    cpu_time_seconds: float,
) -> None:
    try:
        if resource is not None:
            if cpu_time_seconds:
                seconds = max(int(cpu_time_seconds), 1)
                resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
            if memory_limit_mb:
                limit_bytes = max(memory_limit_mb, 1) * 1024 * 1024
                try:
                    resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
                except (ValueError, OSError):  # pragma: no cover - kernel policies
                    pass
                try:
                    resource.setrlimit(resource.RLIMIT_DATA, (limit_bytes, limit_bytes))
                except (ValueError, OSError):  # pragma: no cover - kernel policies
                    pass
        from agents.razar import ai_invoker as remote_ai_invoker

        result = remote_ai_invoker.handover(context=ctx, config_path=config_path)
    except Exception as exc:  # pragma: no cover - defensive
        queue_out.put({"status": "error", "error": repr(exc)})
    else:
        queue_out.put({"status": "ok", "result": result})


def _invoke_remote_agent_sandboxed(
    ctx: Dict[str, Any] | None,
    config_path: Path | str | None,
    *,
    timeout: float = _SANDBOX_TIMEOUT_SECONDS,
    memory_limit_mb: int = _SANDBOX_MEMORY_LIMIT_MB,
) -> Any | None:
    mp_ctx = multiprocessing.get_context("spawn")
    queue_out: multiprocessing.Queue = mp_ctx.Queue()
    process = mp_ctx.Process(
        target=_remote_agent_worker,
        args=(queue_out, ctx, config_path, memory_limit_mb, timeout),
        name="razar_remote_agent",
    )
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.terminate()
        process.join()
        queue_out.close()
        queue_out.join_thread()
        LOGGER.error(
            "Remote agent invocation exceeded timeout after %.1f seconds", timeout
        )
        return None
    try:
        message = queue_out.get(timeout=1.0)
    except queue.Empty:
        LOGGER.error("Remote agent invocation produced no output")
        result = None
    else:
        status = message.get("status")
        if status == "ok":
            result = message.get("result")
        else:
            LOGGER.error(
                "Remote agent invocation failed: %s",
                message.get("error", "unknown error"),
            )
            result = None
    finally:
        queue_out.close()
        queue_out.join_thread()
    exit_code = process.exitcode
    if exit_code not in (0, None):
        LOGGER.warning("Remote agent process exited with code %s", exit_code)
    return result


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
    from agents.razar import code_repair

    ctx: Dict[str, Any] = {"component": component, "error": error}
    if context:
        history = context.get("history")
        if history:
            existing = ctx.setdefault("history", [])
            existing.extend(history)
        ctx.update({k: v for k, v in context.items() if k != "history"})

    config_target = _normalize_config_path(config_path)
    active = _active_agent(config_target)
    normalized_agent = active or "remote_agent"

    suggestion: Any | None = None
    if use_opencode is None:
        use_opencode = normalized_agent not in {"kimi2", "airstar", "rstar"}

    if use_opencode:
        normalized_agent = "opencode"
        payload = json.dumps(ctx)
        start = time.perf_counter()
        try:
            result = subprocess.run(
                ["opencode", "run", "--json"],
                input=payload,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            duration = time.perf_counter() - start
            metrics.observe_agent_latency("opencode_cli", duration)
            LOGGER.info(
                "opencode CLI not found; falling back to library",
                extra={
                    "component": component,
                    "duration": duration,
                    "strategy": "cli",
                },
            )
            client_start = time.perf_counter()
            try:
                diff = opencode_client.complete(payload)
            except Exception:  # pragma: no cover - defensive
                client_duration = time.perf_counter() - client_start
                metrics.observe_agent_latency("opencode_client", client_duration)
                LOGGER.exception("opencode client failed for %s", component)
                return False
            client_duration = time.perf_counter() - client_start
            metrics.observe_agent_latency("opencode_client", client_duration)
            LOGGER.info(
                "opencode client completed",
                extra={
                    "component": component,
                    "duration": client_duration,
                    "strategy": "client",
                },
            )
            suggestion = _diff_to_suggestions(diff, error)
        except Exception:  # pragma: no cover - defensive
            duration = time.perf_counter() - start
            metrics.observe_agent_latency("opencode_cli", duration)
            LOGGER.exception("opencode CLI failed for %s", component)
            return False
        else:
            duration = time.perf_counter() - start
            metrics.observe_agent_latency("opencode_cli", duration)
            LOGGER.info(
                "opencode CLI completed",
                extra={
                    "component": component,
                    "duration": duration,
                    "strategy": "cli",
                    "returncode": result.returncode,
                },
            )
            if result.returncode != 0:
                LOGGER.error(
                    "opencode exited with code %s; using library fallback",
                    result.returncode,
                )
                client_start = time.perf_counter()
                try:
                    diff = opencode_client.complete(payload)
                except Exception:  # pragma: no cover - defensive
                    client_duration = time.perf_counter() - client_start
                    metrics.observe_agent_latency("opencode_client", client_duration)
                    LOGGER.exception("opencode client failed for %s", component)
                    return False
                client_duration = time.perf_counter() - client_start
                metrics.observe_agent_latency("opencode_client", client_duration)
                LOGGER.info(
                    "opencode client completed",
                    extra={
                        "component": component,
                        "duration": client_duration,
                        "strategy": "client",
                        "source": "cli_fallback",
                    },
                )
                suggestion = _diff_to_suggestions(diff, error)
            else:
                try:
                    suggestion = json.loads(result.stdout or "null")
                except json.JSONDecodeError:
                    LOGGER.warning("Could not decode opencode output for %s", component)
                    return False
    else:
        start = time.perf_counter()
        suggestion = _invoke_remote_agent_sandboxed(
            ctx, config_target, timeout=_SANDBOX_TIMEOUT_SECONDS
        )
        duration = time.perf_counter() - start
        metrics.observe_agent_latency(normalized_agent, duration)
        LOGGER.info(
            "Remote agent invocation finished",
            extra={
                "component": component,
                "agent": normalized_agent,
                "duration": duration,
                "strategy": "remote_agent",
                "suggestion_present": bool(suggestion),
            },
        )
        if suggestion is None:
            LOGGER.error(
                "Sandboxed remote agent returned no suggestion for %s",
                component,
            )
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
