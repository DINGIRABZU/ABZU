"""Shared JSON-line logger for RAZAR AI invocation events."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Mapping

from .. import metrics
from ..bootstrap_utils import LOGS_DIR

LOGGER = logging.getLogger(__name__)

INVOCATION_LOG_PATH = LOGS_DIR / "razar_ai_invocations.json"

_LOCK = RLock()
_LEGACY_CONVERTED = False
_AGENT_LOG_PATCHED = False
_AGENT_LOG_FALLBACK: Callable[[Any, Mapping[str, Any]], None] | None = None

__all__ = [
    "INVOCATION_LOG_PATH",
    "append_invocation_event",
    "load_invocation_history",
    "log_invocation",
]


def _isoformat(timestamp: float) -> str:
    """Return an ISO-8601 string (UTC) for ``timestamp`` seconds."""

    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_timestamp_string(value: str, fallback: float) -> float:
    """Return a numeric timestamp parsed from ``value`` or ``fallback``."""

    try:
        return float(value)
    except ValueError:
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(cleaned)
        except ValueError:
            return fallback
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.timestamp()


def _stamp_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``entry`` with normalized timestamps and default status."""

    record = dict(entry)
    now = time.time()
    timestamp = record.get("timestamp")
    if isinstance(timestamp, (int, float)):
        ts_value = float(timestamp)
    elif isinstance(timestamp, str):
        ts_value = _parse_timestamp_string(timestamp, now)
        record["timestamp"] = ts_value
    else:
        ts_value = now
        record["timestamp"] = ts_value

    record.setdefault("timestamp_iso", _isoformat(ts_value))

    if "patched" in record and "status" not in record:
        patched_value = record.get("patched")
        if isinstance(patched_value, bool):
            record["status"] = "success" if patched_value else "failure"

    return record


def _ensure_legacy_conversion() -> None:
    """Convert legacy list-based logs to JSON lines."""

    global _LEGACY_CONVERTED
    if _LEGACY_CONVERTED:
        return

    if not INVOCATION_LOG_PATH.exists():
        _LEGACY_CONVERTED = True
        return

    try:
        raw = INVOCATION_LOG_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        LOGGER.debug("Could not read %s: %s", INVOCATION_LOG_PATH, exc)
        _LEGACY_CONVERTED = True
        return

    stripped = raw.lstrip()
    if not stripped:
        _LEGACY_CONVERTED = True
        return

    if stripped.startswith("["):
        try:
            records = json.loads(raw)
        except json.JSONDecodeError as exc:
            LOGGER.warning(
                "Failed to parse legacy invocation log %s: %s",
                INVOCATION_LOG_PATH,
                exc,
            )
            _LEGACY_CONVERTED = True
            return

        INVOCATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with INVOCATION_LOG_PATH.open("w", encoding="utf-8") as handle:
            for record in records:
                if isinstance(record, dict):
                    normalized = _stamp_entry(record)
                    handle.write(json.dumps(normalized, sort_keys=True))
                    handle.write("\n")
        LOGGER.info("Converted legacy invocation log at %s", INVOCATION_LOG_PATH)

    _LEGACY_CONVERTED = True


def append_invocation_event(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Append ``entry`` to the invocation log and return the stored record."""

    record = _stamp_entry(entry)
    with _LOCK:
        _ensure_legacy_conversion()
        INVOCATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with INVOCATION_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")
    return record


def _patch_agent_append_log() -> None:
    """Redirect `agents.razar.ai_invoker._append_log` to JSON-line output."""

    global _AGENT_LOG_PATCHED, _AGENT_LOG_FALLBACK
    if _AGENT_LOG_PATCHED:
        return
    try:
        from agents.razar import ai_invoker as agent_ai_invoker
    except Exception:  # pragma: no cover - optional dependency
        return

    original = getattr(agent_ai_invoker, "_append_log", None)
    if not callable(original):
        return
    if getattr(original, "__module__", "") == __name__:
        _AGENT_LOG_PATCHED = True
        return

    _AGENT_LOG_FALLBACK = original

    def _append_log_proxy(path: Any, entry: Mapping[str, Any]) -> None:
        try:
            target = Path(path)
        except TypeError:
            target = Path(str(path))
        if target == INVOCATION_LOG_PATH:
            append_invocation_event(entry)
            return
        fallback = _AGENT_LOG_FALLBACK
        if fallback is not None:
            fallback(path, entry)

    agent_ai_invoker._append_log = _append_log_proxy  # type: ignore[attr-defined]
    _AGENT_LOG_PATCHED = True


def log_invocation(
    component: str,
    attempt: int,
    error: str,
    patched: bool,
    *,
    event: str | None = "attempt",
    agent: str | None = None,
    agent_original: str | None = None,
    retries: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Record an AI handover attempt and update metrics."""

    entry: dict[str, Any] = {
        "component": component,
        "attempt": int(attempt),
        "error": error,
        "patched": bool(patched),
    }
    if event is not None:
        entry["event"] = event
    if agent is not None:
        entry["agent"] = agent
    if agent_original is not None:
        entry["agent_original"] = agent_original
    if retries is not None:
        entry["retries"] = retries
    if extra:
        entry.update(extra)

    record = append_invocation_event(entry)

    retry_count = retries if retries is not None else max(int(attempt) - 1, 0)
    metrics.record_invocation(
        component or "unknown", record["patched"], retries=retry_count
    )

    return record


def load_invocation_history(
    component: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return invocation records filtered by ``component``."""

    with _LOCK:
        _ensure_legacy_conversion()
        if not INVOCATION_LOG_PATH.exists():
            return []
        try:
            lines = INVOCATION_LOG_PATH.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            LOGGER.debug("Could not read %s: %s", INVOCATION_LOG_PATH, exc)
            return []

    entries: list[dict[str, Any]] = []
    target = component.lower() if isinstance(component, str) else None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        record = _stamp_entry(data)
        if target is not None:
            current = str(record.get("component", "")).lower()
            if current != target:
                continue
        elif "component" not in record:
            continue
        entries.append(record)

    entries.sort(key=lambda item: item.get("timestamp", 0.0))
    if limit is not None and limit > 0:
        entries = entries[-limit:]
    return entries


_patch_agent_append_log()
