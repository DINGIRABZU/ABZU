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
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Sequence
from uuid import uuid4

import inspect

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)

try:  # pragma: no cover - optional dependency used for upload route
    import multipart  # type: ignore[unused-import]  # noqa: F401

    _HAS_MULTIPART = True
except Exception:  # pragma: no cover - multipart dependency missing in sandbox
    _HAS_MULTIPART = False

try:  # pragma: no cover - optional metrics shim
    from opentelemetry import metrics, trace
except ImportError:  # pragma: no cover - fallback to repo stub without metrics
    metrics = None  # type: ignore[assignment]
    from opentelemetry import trace  # type: ignore[no-redef]
try:  # pragma: no cover - optional trace status shim
    from opentelemetry.trace import Status, StatusCode
except ImportError:  # pragma: no cover - fallback when Status classes missing

    class StatusCode(Enum):
        OK = "OK"
        ERROR = "ERROR"

    class Status:  # type: ignore[override]
        def __init__(self, status_code: StatusCode, description: str | None = None):
            self.status_code = status_code
            self.description = description


from agents.operator_dispatcher import OperatorDispatcher
from agents.interaction_log import log_agent_interaction
from bana import narrative as bana_narrative
from agents.task_orchestrator import run_mission
from fastapi.responses import HTMLResponse, JSONResponse
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
    ROTATION_WINDOW_HOURS,
    OperatorMCPAdapter,
    load_rotation_history,
    latest_rotation_entry,
    normalize_handshake_for_trace,
    compute_handshake_checksum,
    record_rotation_drill,
    stage_b_context_enabled,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_tracer = trace.get_tracer(__name__)
_meter = metrics.get_meter(__name__) if metrics is not None else None

if _meter is not None:
    try:
        _transport_latency = _meter.create_histogram(
            "operator_api_transport_latency_ms",
            unit="ms",
            description="Latency for operator_api operations segmented by transport.",
        )
    except Exception:  # pragma: no cover - metrics provider missing
        _transport_latency = None

    try:
        _transport_errors = _meter.create_counter(
            "operator_api_transport_errors_total",
            description=(
                "Total operator_api transport errors grouped by operation and reason."
            ),
        )
    except Exception:  # pragma: no cover - metrics provider missing
        _transport_errors = None

    try:
        _transport_fallbacks = _meter.create_counter(
            "operator_api_transport_fallback_total",
            description="Count of fallback executions by transport and operation.",
        )
    except Exception:  # pragma: no cover - metrics provider missing
        _transport_fallbacks = None
else:  # pragma: no cover - metrics API unavailable
    _transport_latency = None
    _transport_errors = None
    _transport_fallbacks = None

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


class CommandValidationError(ValueError):
    """Raised when a command payload is missing required fields."""


class CommandDispatchError(RuntimeError):
    """Raised when the dispatcher encounters an unexpected failure."""


class MCPHandshakeError(RuntimeError):
    """Raised when the MCP handshake fails for a transport request."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _record_latency(operation: str, transport: str, duration_ms: float) -> None:
    if _transport_latency is None:  # pragma: no cover - metrics disabled
        return
    try:
        _transport_latency.record(
            duration_ms,
            {"operation": operation, "transport": transport},
        )
    except Exception:  # pragma: no cover - metrics provider failure
        logger.debug("failed to record latency metric", exc_info=True)


def _record_error(operation: str, transport: str, reason: str) -> None:
    if _transport_errors is None:  # pragma: no cover - metrics disabled
        return
    try:
        _transport_errors.add(
            1,
            {"operation": operation, "transport": transport, "reason": reason},
        )
    except Exception:  # pragma: no cover - metrics provider failure
        logger.debug("failed to record error metric", exc_info=True)


def _record_fallback(operation: str, transport: str) -> None:
    if _transport_fallbacks is None:  # pragma: no cover - metrics disabled
        return
    try:
        _transport_fallbacks.add(
            1,
            {"operation": operation, "transport": transport},
        )
    except Exception:  # pragma: no cover - metrics provider failure
        logger.debug("failed to record fallback metric", exc_info=True)


_REPO_ROOT = Path(__file__).resolve().parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"

_STAGE_A_ROOT = _REPO_ROOT / "logs" / "stage_a"
_STAGE_B_ROOT = _REPO_ROOT / "logs" / "stage_b"
_STAGE_C_ROOT = _REPO_ROOT / "logs" / "stage_c"
_STAGE_E_ROOT = _REPO_ROOT / "logs" / "stage_e"

_STAGE_E_CONNECTORS: tuple[str, ...] = (
    "operator_api",
    "operator_upload",
    "crown_handshake",
)
_STAGE_E_DASHBOARD_URL = os.getenv(
    "ABZU_STAGE_E_DASHBOARD_URL",
    "https://grafana.ops.abzu.dev/d/operator-transport-parity/continuous-stage-e",
)
_STAGE_C_BUNDLE_FILENAME = "readiness_bundle.json"
_STAGE_C_SUMMARY_FILENAME = "summary.json"
_STAGE_C3_SLUG = "stage_c3_readiness_sync"


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


StageMetricsExtractor = Callable[
    [str, str, Path, dict[str, Any]],
    Awaitable[dict[str, Any] | None] | dict[str, Any] | None,
]


def _sanitize_for_json(value: Any) -> Any:
    """Return ``value`` converted to JSON-serialisable primitives."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(k): _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in value]
    return str(value)


CommandBuilder = Callable[[Path], Sequence[str]]


async def _run_stage_workflow(
    stage_root: Path,
    slug: str,
    command: Sequence[str] | CommandBuilder,
    *,
    metrics_extractor: StageMetricsExtractor | None = None,
) -> dict[str, Any]:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slug}"
    log_dir = stage_root / run_id
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_path = log_dir / f"{slug}.stdout.log"
    stderr_path = log_dir / f"{slug}.stderr.log"
    summary_path = log_dir / "summary.json"

    started_at = datetime.now(timezone.utc)

    if callable(command):
        command_args = list(command(log_dir))
    else:
        command_args = list(command)

    env = os.environ.copy()
    pythonpath_parts = [str(_REPO_ROOT)]
    src_dir = _REPO_ROOT / "src"
    if src_dir.exists():
        pythonpath_parts.append(str(src_dir))
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    env["ABZU_FORCE_STAGE_SANDBOX"] = "1"

    try:
        process = await asyncio.create_subprocess_exec(
            *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
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
            "command": command_args,
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

    summary_line = ""
    summary_json: Mapping[str, Any] | None = None
    json_buffer: list[str] = []
    collecting_json = False
    for line in reversed(stdout_lines):
        stripped = line.strip()
        if not stripped:
            if collecting_json:
                json_buffer.insert(0, line)
            continue
        if not summary_line:
            summary_line = stripped
        if summary_json is not None:
            break

        should_collect = collecting_json or stripped.startswith(("{", "}"))
        if should_collect:
            if not collecting_json:
                collecting_json = True
            json_buffer.insert(0, line)
            candidate_text = "\n".join(json_buffer).strip()
            if (
                candidate_text.startswith("{")
                and candidate_text.endswith("}")
                and candidate_text.count("{") == candidate_text.count("}")
            ):
                try:
                    candidate = json.loads(candidate_text)
                except json.JSONDecodeError:
                    continue
                if isinstance(candidate, Mapping):
                    summary_json = candidate
                    break
            continue

        json_buffer.clear()
        collecting_json = False

    payload = {
        "status": "success" if process.returncode == 0 else "error",
        "stage": slug,
        "run_id": run_id,
        "command": command_args,
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
    if summary_json is not None:
        payload["summary"] = summary_json
        status_override = summary_json.get("status")
        if isinstance(status_override, str):
            payload["status"] = status_override
        warnings = summary_json.get("warnings")
        if warnings is not None:
            payload["warnings"] = warnings
    elif summary_line:
        payload["summary"] = summary_line
    if stderr_text.strip():
        payload["stderr"] = stderr_text
    if payload["status"] == "error":
        payload.setdefault("error", f"{slug} exited with code {process.returncode}")

    if metrics_extractor is not None:
        try:
            metrics = metrics_extractor(stdout_text, stderr_text, log_dir, payload)
            if inspect.isawaitable(metrics):
                metrics = await metrics
            if metrics is not None:
                payload["metrics"] = metrics
        except Exception as exc:  # pragma: no cover - defensive metrics parsing
            payload["metrics_error"] = str(exc)
            payload["status"] = "error"
            payload.setdefault("error", f"{slug} metrics extraction failed: {exc}")

    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["summary_path"] = str(summary_path)
    return payload


def _normalise_artifact_mapping(value: Any) -> dict[str, str] | None:
    """Return ``value`` coerced into a string-keyed mapping of artifact paths."""

    if isinstance(value, Mapping):
        return {str(key): str(val) for key, val in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return {f"artifact_{index + 1}": str(item) for index, item in enumerate(value)}
    if value is None:
        return None
    return {"artifact": str(value)}


def _attach_summary_artifacts(payload: dict[str, Any]) -> dict[str, Any]:
    """Ensure ``payload`` exposes artifact paths at the top level for UI consumers."""

    if not isinstance(payload, Mapping):
        return payload

    artifacts = payload.get("artifacts")
    if isinstance(artifacts, Mapping) and artifacts:
        return payload

    summary = payload.get("summary")
    summary_mapping = summary if isinstance(summary, Mapping) else None
    if summary_mapping is None:
        return payload

    normalised = _normalise_artifact_mapping(summary_mapping.get("artifacts"))
    if normalised:
        payload["artifacts"] = normalised
    return payload


def _extract_json_from_stdout(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("{"):
            candidate = "\n".join(lines[index:]).strip()
            if not candidate:
                continue
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON payload found in command stdout")


def _seconds_to_ms(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number * 1000.0, 3)


def _stage_b1_metrics(
    stdout_text: str,
    _stderr_text: str,
    _log_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    summary = _extract_json_from_stdout(stdout_text)
    stubbed_bundle = bool(summary.get("stubbed_bundle"))
    fallback_reason = summary.get("fallback_reason")
    latency_ms = {
        "p50": _seconds_to_ms(summary.get("latency_p50_s")),
        "p95": _seconds_to_ms(summary.get("latency_p95_s")),
        "p99": _seconds_to_ms(summary.get("latency_p99_s")),
    }
    layers = summary.get("layers")
    if isinstance(layers, Mapping):
        layer_summary = {
            "total": layers.get("total"),
            "ready": layers.get("ready"),
            "failed": layers.get("failed"),
        }
    else:
        layer_summary = None
    return {
        "dataset": summary.get("dataset"),
        "total_records": summary.get("total_records"),
        "queries_timed": summary.get("queries_timed"),
        "latency_ms": latency_ms,
        "layers": layer_summary,
        "query_failures": summary.get("query_failures"),
        "stubbed_bundle": stubbed_bundle,
        "fallback_reason": fallback_reason,
    }


def _stage_b2_metrics(
    _stdout_text: str,
    _stderr_text: str,
    log_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    packet_path = _REPO_ROOT / "logs" / "stage_b_rehearsal_packet.json"
    if not packet_path.exists():
        raise FileNotFoundError(
            "Stage B rehearsal packet not found at logs/stage_b_rehearsal_packet.json"
        )
    data = json.loads(packet_path.read_text(encoding="utf-8"))
    destination = log_dir / packet_path.name
    destination.write_text(json.dumps(data, indent=2), encoding="utf-8")
    artifacts = payload.setdefault("artifacts", {})
    artifacts["rehearsal_packet"] = str(destination)

    connectors_summary: dict[str, Any] = {}
    connectors = data.get("connectors", {})
    dropout_connectors: list[str] = []
    fallback_warnings: list[str] = []

    def _truthy(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.strip().lower() not in {"", "0", "false", "none"}
        return True

    if isinstance(connectors, Mapping):
        for connector_id, record in connectors.items():
            if not isinstance(record, Mapping):
                continue
            connector_key = str(connector_id)
            handshake = record.get("handshake_response")
            if isinstance(handshake, Mapping):
                accepted = handshake.get("accepted_contexts")
            else:
                accepted = None

            doctrine_failures = record.get("doctrine_failures")
            if doctrine_failures:
                if isinstance(doctrine_failures, Sequence) and not isinstance(
                    doctrine_failures, (str, bytes)
                ):
                    details = ", ".join(str(item) for item in doctrine_failures)
                else:
                    details = str(doctrine_failures)
                fallback_warnings.append(
                    f"{connector_key}: doctrine deviations recorded ({details})"
                )

            fallback_entries = record.get("fallbacks")
            if isinstance(fallback_entries, Sequence) and not isinstance(
                fallback_entries, (str, bytes)
            ):
                if fallback_entries:
                    fallback_warnings.append(
                        f"{connector_key}: fallback hints -> "
                        + ", ".join(str(item) for item in fallback_entries)
                    )

            heartbeat = record.get("heartbeat_payload")
            if isinstance(heartbeat, Mapping):
                if (
                    _truthy(heartbeat.get("dropout"))
                    or _truthy(heartbeat.get("dropouts_detected"))
                    or _truthy(heartbeat.get("dropouts"))
                ):
                    dropout_connectors.append(connector_key)

                heartbeat_fallback = heartbeat.get("fallback")
                if heartbeat_fallback:
                    fallback_warnings.append(
                        f"{connector_key}: heartbeat fallback -> {heartbeat_fallback}"
                    )
                heartbeat_fallbacks = heartbeat.get("fallbacks")
                if isinstance(heartbeat_fallbacks, Sequence) and not isinstance(
                    heartbeat_fallbacks, (str, bytes)
                ):
                    if heartbeat_fallbacks:
                        fallback_warnings.append(
                            f"{connector_key}: heartbeat fallbacks -> "
                            + ", ".join(str(item) for item in heartbeat_fallbacks)
                        )

            connectors_summary[connector_key] = {
                "module": record.get("module"),
                "doctrine_ok": record.get("doctrine_ok"),
                "supported_channels": record.get("supported_channels"),
                "capabilities": record.get("capabilities"),
                "accepted_contexts": accepted,
            }

    dropout_connectors = sorted(set(dropout_connectors))
    fallback_warnings = [warning for warning in fallback_warnings if warning.strip()]

    return {
        "generated_at": data.get("generated_at"),
        "stage": data.get("stage"),
        "context": data.get("context"),
        "connectors": connectors_summary,
        "dropouts_detected": len(dropout_connectors),
        "dropout_connectors": dropout_connectors,
        "fallback_warnings": fallback_warnings,
    }


def _stage_b3_metrics(
    stdout_text: str,
    _stderr_text: str,
    log_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    result = _extract_json_from_stdout(stdout_text)

    rotation_log = _REPO_ROOT / "logs" / "stage_b_rotation_drills.jsonl"
    rotation_history: list[dict[str, Any]] = []
    if rotation_log.exists():
        try:
            rotation_history = load_rotation_history()
        except json.JSONDecodeError:  # pragma: no cover - defensive parsing
            logger.warning("unable to parse rotation drill ledger", exc_info=True)
            rotation_history = []

    handshake = result.get("handshake")
    accepted_contexts = None
    session_info = None
    if isinstance(handshake, Mapping):
        accepted_contexts = handshake.get("accepted_contexts")
        session_info = handshake.get("session")

    heartbeat = result.get("heartbeat")
    heartbeat_payload = None
    credential_expiry = None
    if isinstance(heartbeat, Mapping):
        heartbeat_payload = heartbeat.get("payload")
        credential_expiry = heartbeat.get("credential_expiry")

    targets_raw = result.get("targets")
    connectors: list[str] = []
    if isinstance(targets_raw, Sequence) and not isinstance(targets_raw, (str, bytes)):
        connectors = [str(target) for target in targets_raw]

    rotation_ledger_raw = result.get("rotation_ledger")
    ledger_entries: dict[str, Mapping[str, Any]] = {}
    if isinstance(rotation_ledger_raw, Mapping):
        for connector_id, entry in rotation_ledger_raw.items():
            if isinstance(connector_id, str) and isinstance(entry, Mapping):
                ledger_entries[connector_id] = dict(entry)

    latest_indices: dict[str, int] = {}
    for index, entry in enumerate(rotation_history):
        connector_id = entry.get("connector_id")
        if isinstance(connector_id, str):
            latest_indices[connector_id] = index

    connector_entries: list[Mapping[str, Any]] = []
    for connector_id in connectors:
        ledger_entry = ledger_entries.get(connector_id)
        if ledger_entry is not None:
            connector_entries.append(ledger_entry)
            continue
        index = latest_indices.get(connector_id)
        if index is not None:
            connector_entries.append(rotation_history[index])
    if not connector_entries:
        if ledger_entries:
            connector_entries.extend(ledger_entries.values())
        elif rotation_history:
            connector_entries.append(rotation_history[-1])

    rotation_window_info: Mapping[str, Any] | None = None
    for entry in reversed(connector_entries):
        rotation_window = entry.get("rotation_window")
        if isinstance(rotation_window, Mapping):
            rotation_window_info = dict(rotation_window)
            break

    rotation_window_id = None
    rotation_window_expires = None
    if isinstance(rotation_window_info, Mapping):
        rotation_window_id = rotation_window_info.get("window_id")
        rotation_window_expires = rotation_window_info.get("expires_at")

    if credential_expiry is None and isinstance(session_info, Mapping):
        session_expiry = session_info.get("credential_expiry")
        if isinstance(session_expiry, str):
            credential_expiry = session_expiry

    doctrine_ok = result.get("doctrine_ok")
    if doctrine_ok is True:
        doctrine_text = "doctrine ok"
    elif doctrine_ok is False:
        failures = result.get("doctrine_failures")
        failure_text = ""
        if isinstance(failures, Sequence) and not isinstance(failures, (str, bytes)):
            failure_text = ", ".join(str(item) for item in failures if item)
        elif failures:
            failure_text = str(failures)
        doctrine_text = (
            f"doctrine issues: {failure_text}" if failure_text else "doctrine issues"
        )
    else:
        doctrine_text = "doctrine status unknown"

    connector_text = "/".join(connectors) if connectors else "no connectors reported"
    window_text = (
        f"window {rotation_window_id}" if rotation_window_id else "window unknown"
    )
    expiry_segments: list[str] = []
    if rotation_window_expires:
        expiry_segments.append(f"rotation expires {rotation_window_expires}")
    if credential_expiry:
        expiry_segments.append(f"credentials expire {credential_expiry}")
    expiry_text = "; ".join(expiry_segments)

    summary_parts = [f"Rotated {connector_text} ({doctrine_text})", window_text]
    if expiry_text:
        summary_parts.append(expiry_text)
    rotation_summary = "; ".join(summary_parts)
    payload["summary"] = rotation_summary

    if rotation_history and rotation_summary:
        updated = False
        ledger_connectors = set(connectors) if connectors else set()
        default_connector = (
            rotation_history[-1].get("connector_id") if rotation_history else None
        )
        ledger_targets = ledger_connectors or {default_connector}
        for connector_id in ledger_targets:
            index = latest_indices.get(connector_id)
            if index is None:
                continue
            entry = dict(rotation_history[index])
            entry["rotation_summary"] = rotation_summary
            if credential_expiry:
                entry["credential_expiry"] = credential_expiry
            rotation_history[index] = entry
            updated = True
        if updated:
            with rotation_log.open("w", encoding="utf-8") as handle:
                for item in rotation_history:
                    handle.write(json.dumps(item) + "\n")

    if rotation_log.exists():
        destination = log_dir / rotation_log.name
        shutil.copy2(rotation_log, destination)
        artifacts = payload.setdefault("artifacts", {})
        artifacts["rotation_log"] = str(destination)

    return {
        "stage": result.get("stage"),
        "targets": result.get("targets"),
        "doctrine_ok": result.get("doctrine_ok"),
        "doctrine_failures": result.get("doctrine_failures"),
        "accepted_contexts": accepted_contexts,
        "session": session_info,
        "heartbeat_payload": heartbeat_payload,
        "heartbeat_expiry": credential_expiry,
        "rotation_window": rotation_window_info,
        "rotation_summary": rotation_summary,
    }


def _stage_c1_metrics(
    stdout_text: str,
    _stderr_text: str,
    _log_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    stdout_lines = [line.strip() for line in stdout_text.splitlines() if line.strip()]
    checklist_path_value = os.environ.get("ABSOLUTE_PROTOCOL_CHECKLIST_PATH")
    if checklist_path_value:
        checklist_path = Path(checklist_path_value)
        if not checklist_path.is_absolute():
            checklist_path = (_REPO_ROOT / checklist_path).resolve()
    else:
        checklist_path = _REPO_ROOT / "docs" / "absolute_protocol_checklist.md"

    checklist_lines: list[str] = []
    try:
        if checklist_path.exists():
            checklist_lines = [
                line.strip()
                for line in checklist_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    except OSError:
        checklist_lines = []

    lines = stdout_lines + checklist_lines
    unchecked = [line for line in lines if line.startswith("- [ ]")]
    status_failure_pattern = re.compile(r"status:\s*(failed|blocked)\b", re.IGNORECASE)
    failing: list[str] = []
    seen_failures: set[str] = set()
    for index, line in enumerate(lines):
        if not status_failure_pattern.search(line):
            continue
        if line.startswith("- ["):
            if line not in seen_failures:
                failing.append(line)
                seen_failures.add(line)
            continue

        if line not in seen_failures:
            failing.append(line)
            seen_failures.add(line)

        if index > 0:
            parent = lines[index - 1]
            if parent.startswith("- [") and parent not in seen_failures:
                failing.append(parent)
                seen_failures.add(parent)
    completed = not unchecked and not failing
    summary_line = next(
        (line for line in reversed(stdout_lines) if not line.startswith("- [ ]")), ""
    )
    metrics = {
        "completed": completed,
        "unchecked_count": len(unchecked),
        "unchecked_items": unchecked,
        "failing_count": len(failing),
        "failing_items": failing,
        "message": summary_line or None,
    }
    payload["failures"] = failing
    if failing:
        payload["error"] = "checklist contains failing items"
        payload["status"] = "error"
    elif not completed:
        payload["error"] = "checklist contains unchecked items"
        payload["status"] = "error"
    return metrics


def _stage_c2_metrics(
    _stdout_text: str,
    _stderr_text: str,
    log_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    output_dir = log_dir / "demo_storyline"
    telemetry_dir = output_dir / "telemetry"
    summary_path = telemetry_dir / "summary.json"
    run_summary_path = telemetry_dir / "run_summary.json"
    manifest_path = telemetry_dir / "media_manifest.json"
    events_path = telemetry_dir / "events.jsonl"
    emotion_path = output_dir / "emotion" / "stream.jsonl"

    metrics: dict[str, Any] = {
        "output_dir": str(output_dir),
        "summary": None,
        "telemetry_events": str(events_path) if events_path.exists() else None,
        "emotion_stream": str(emotion_path) if emotion_path.exists() else None,
        "media_manifest": str(manifest_path) if manifest_path.exists() else None,
        "run_summary": str(run_summary_path) if run_summary_path.exists() else None,
    }

    if summary_path.exists():
        metrics["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        payload["error"] = f"demo summary missing at {summary_path}"
        payload["status"] = "error"

    artifacts = payload.setdefault("artifacts", {})
    for label, path in (
        ("summary", summary_path),
        ("run_summary", run_summary_path),
        ("telemetry_events", events_path),
        ("emotion_stream", emotion_path),
        ("media_manifest", manifest_path),
    ):
        if path.exists():
            artifacts[label] = str(path)

    return metrics


def _latest_stage_summary(
    stage_root: Path,
) -> tuple[Path | None, dict[str, Any] | None]:
    if not stage_root.exists():
        return None, None
    summary_files = sorted(stage_root.glob("*/summary.json"))
    if not summary_files:
        return None, None
    latest = max(summary_files)
    data = json.loads(latest.read_text(encoding="utf-8"))
    return latest, data


def _stage_c3_metrics(
    _stdout_text: str,
    _stderr_text: str,
    _log_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    bundle_path = _log_dir / _STAGE_C_BUNDLE_FILENAME
    summary_path = _log_dir / _STAGE_C_SUMMARY_FILENAME
    bundle_data: dict[str, Any] | None = None
    metrics: dict[str, Any] = {
        "bundle_path": str(bundle_path) if bundle_path.exists() else None,
        "summary_path": str(summary_path) if summary_path.exists() else None,
    }

    if bundle_path.exists():
        try:
            bundle_data = json.loads(bundle_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive parse
            payload["status"] = "error"
            payload["error"] = f"invalid readiness bundle: {exc}"
            metrics["bundle_error"] = str(exc)

    if bundle_data:
        stage_a_section = dict(bundle_data.get("stage_a") or {})
        stage_b_section = dict(bundle_data.get("stage_b") or {})
        if bundle_data.get("generated_at"):
            metrics["generated_at"] = bundle_data["generated_at"]
        missing_entries = list(bundle_data.get("missing") or [])
    else:
        from scripts import aggregate_stage_readiness as readiness_aggregate

        stage_a_section, stage_a_missing = readiness_aggregate._build_stage_a_snapshot()
        stage_b_path, stage_b_summary = readiness_aggregate._latest_summary(
            readiness_aggregate.STAGE_B_ROOT
        )
        stage_b_section = readiness_aggregate._build_stage_snapshot(
            "stage_b", stage_b_path, stage_b_summary
        )
        missing_entries = list(stage_a_missing)
        if not stage_b_section.get("summary"):
            missing_entries.append("stage_b")

    metrics["missing"] = missing_entries

    def _ensure_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if value is None:
            return []
        return [str(value)]

    stage_a_notes = _ensure_list(stage_a_section.get("risk_notes"))
    stage_b_notes = _ensure_list(stage_b_section.get("risk_notes"))

    def _list_has_risk(notes: Sequence[str]) -> bool:
        return any(str(item).strip() for item in notes)

    stage_a_has_risk = _list_has_risk(stage_a_notes)
    stage_b_has_risk = _list_has_risk(stage_b_notes)

    stage_a_slugs_raw = stage_a_section.get("slugs")
    normalized_stage_a_slugs: dict[str, dict[str, Any]] = {}
    if isinstance(stage_a_slugs_raw, Mapping):
        for slug, slug_section in stage_a_slugs_raw.items():
            if not isinstance(slug_section, Mapping):
                continue
            slug_key = str(slug).upper()
            slug_summary = slug_section.get("summary")
            if not isinstance(slug_summary, Mapping):
                slug_summary = None
            slug_notes = _ensure_list(slug_section.get("risk_notes"))
            slug_status = slug_section.get("status")
            if not isinstance(slug_status, str) and slug_summary is not None:
                slug_status = slug_summary.get("status")
            if not isinstance(slug_status, str):
                slug_status = "missing"
            slug_artifacts_value = slug_section.get("artifacts")
            if isinstance(slug_artifacts_value, list):
                slug_artifacts = [str(item) for item in slug_artifacts_value]
            elif slug_artifacts_value is None:
                slug_artifacts = []
            else:
                slug_artifacts = [str(slug_artifacts_value)]
            normalized_stage_a_slugs[slug_key] = {
                "summary": slug_summary,
                "summary_path": slug_section.get("summary_path"),
                "artifacts": slug_artifacts,
                "risk_notes": slug_notes,
                "status": slug_status,
            }

    if not normalized_stage_a_slugs:
        summary = stage_a_section.get("summary")
        summary_mapping = summary if isinstance(summary, Mapping) else None
        slug_status = stage_a_section.get("status")
        if not isinstance(slug_status, str) and summary_mapping is not None:
            slug_status = summary_mapping.get("status")
        if not isinstance(slug_status, str):
            slug_status = "missing"
        fallback_notes = stage_a_notes or ["readiness summary missing"]
        artifacts_value = stage_a_section.get("artifacts")
        if isinstance(artifacts_value, list):
            artifacts_list = [str(item) for item in artifacts_value]
        elif artifacts_value is None:
            artifacts_list = []
        else:
            artifacts_list = [str(artifacts_value)]
        normalized_stage_a_slugs["UNKNOWN"] = {
            "summary": summary_mapping,
            "summary_path": stage_a_section.get("summary_path"),
            "artifacts": artifacts_list,
            "risk_notes": fallback_notes,
            "status": slug_status,
        }

    stage_a_section["slugs"] = normalized_stage_a_slugs

    if not stage_a_notes:
        aggregated = []
        for slug_entry in normalized_stage_a_slugs.values():
            aggregated.extend(slug_entry.get("risk_notes", []))
        stage_a_notes = aggregated
    stage_a_section["risk_notes"] = stage_a_notes

    stage_a_status = stage_a_section.get("status")
    if not isinstance(stage_a_status, str):
        if normalized_stage_a_slugs:
            slug_statuses = [
                entry.get("status", "missing")
                for entry in normalized_stage_a_slugs.values()
            ]
            if slug_statuses and all(status == "success" for status in slug_statuses):
                stage_a_status = "success"
            elif slug_statuses and all(status == "missing" for status in slug_statuses):
                stage_a_status = "missing"
            else:
                stage_a_status = "requires_attention"
        else:
            stage_a_status = "missing"
    stage_a_section["status"] = stage_a_status

    stage_b_status = stage_b_section.get("status")
    stage_b_summary = stage_b_section.get("summary")
    if not isinstance(stage_b_summary, Mapping):
        stage_b_summary = None
    if not isinstance(stage_b_status, str):
        if stage_b_summary is not None:
            status_candidate = stage_b_summary.get("status")
            stage_b_status = (
                status_candidate if isinstance(status_candidate, str) else None
            )
        if not isinstance(stage_b_status, str):
            stage_b_status = "missing"
    stage_b_section["status"] = stage_b_status
    stage_b_section["risk_notes"] = stage_b_notes

    def _coerce_path(value: Any) -> Path | None:
        if isinstance(value, Path):
            return value
        if isinstance(value, str) and value.strip():
            return Path(value)
        return None

    def _preferred_artifact_path(primary: Any, fallback: Any, label: str) -> str | None:
        primary_path = _coerce_path(primary)
        fallback_path = _coerce_path(fallback)
        if primary_path and primary_path.exists():
            return str(primary_path)
        if fallback_path and fallback_path.exists():
            if primary_path:
                logger.warning(
                    "bundle copy missing for %s at %s; using fallback %s",
                    label,
                    primary_path,
                    fallback_path,
                )
            else:
                logger.warning(
                    "bundle copy missing for %s; using fallback %s",
                    label,
                    fallback_path,
                )
            return str(fallback_path)
        if primary_path:
            return str(primary_path)
        if fallback_path:
            logger.warning(
                "bundle artifact missing for %s; no fallback at %s",
                label,
                fallback_path,
            )
        return None

    def _build_merged(
        stage_a: Mapping[str, Any], stage_b: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        stage_a_slugs = (
            stage_a.get("slugs") if isinstance(stage_a.get("slugs"), Mapping) else {}
        )
        stage_a_latest_runs: dict[str, Any] = {}
        stage_a_completed: dict[str, Any] = {}
        stage_a_slug_status: dict[str, str] = {}
        stage_a_slug_notes: dict[str, list[str]] = {}
        for slug, slug_entry in stage_a_slugs.items():
            if not isinstance(slug_entry, Mapping):
                continue
            slug_key = str(slug).upper()
            slug_summary = slug_entry.get("summary")
            if not isinstance(slug_summary, Mapping):
                slug_summary = None
            run_id = None
            completed_at = None
            if slug_summary is not None:
                run_id = slug_summary.get("run_id")
                completed_at = slug_summary.get("completed_at")
            latest_runs_section = stage_a.get("latest_runs")
            if run_id is None and isinstance(latest_runs_section, Mapping):
                run_id = latest_runs_section.get(slug_key)
            completed_section = stage_a.get("completed_at")
            if completed_at is None and isinstance(completed_section, Mapping):
                completed_at = completed_section.get(slug_key)
            stage_a_latest_runs[slug_key] = run_id
            stage_a_completed[slug_key] = completed_at
            stage_a_slug_status[slug_key] = str(slug_entry.get("status", "missing"))
            stage_a_slug_notes[slug_key] = _ensure_list(slug_entry.get("risk_notes"))

        def _notes_present(value: Any) -> bool:
            if value is None:
                return False
            if isinstance(value, str):
                return bool(value.strip())
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return any(_notes_present(item) for item in value)
            return bool(str(value).strip())

        stage_b_summary_mapping = stage_b if isinstance(stage_b, Mapping) else None
        stage_b_run_id = None
        stage_b_completed_at = None
        if stage_b_summary_mapping is not None:
            summary_payload = stage_b_summary_mapping.get("summary")
            if isinstance(summary_payload, Mapping):
                stage_b_run_id = summary_payload.get("run_id")
                stage_b_completed_at = summary_payload.get("completed_at")
            else:
                run_id_candidate = stage_b_summary_mapping.get("latest_runs")
                if isinstance(run_id_candidate, Mapping):
                    stage_b_run_id = run_id_candidate.get("stage_b")
                completed_candidate = stage_b_summary_mapping.get("completed_at")
                if isinstance(completed_candidate, Mapping):
                    stage_b_completed_at = completed_candidate.get("stage_b")

        merged_payload: dict[str, Any] = {
            "latest_runs": {
                "stage_a": stage_a_latest_runs or stage_a.get("latest_runs"),
                "stage_b": stage_b_run_id or stage_b_section.get("latest_runs"),
            },
            "completed_at": {
                "stage_a": stage_a_completed or stage_a.get("completed_at"),
                "stage_b": stage_b_completed_at or stage_b_section.get("completed_at"),
            },
            "status_flags": {
                "stage_a": stage_a_status,
                "stage_b": stage_b_status,
            },
            "risk_notes": {
                "stage_a": stage_a_notes,
                "stage_b": stage_b_notes,
            },
            "stage_a_slugs": {
                slug: {
                    "status": stage_a_slug_status.get(slug, "missing"),
                    "risk_notes": stage_a_slug_notes.get(slug, []),
                }
                for slug in stage_a_slug_status
            },
        }

        rotation_info: dict[str, Any] = {}
        if stage_b_summary is not None:
            summary_text: str | None = None
            metrics_block = stage_b_summary.get("metrics")
            if isinstance(metrics_block, Mapping):
                rotation_summary_value = metrics_block.get("rotation_summary")
                if (
                    isinstance(rotation_summary_value, str)
                    and rotation_summary_value.strip()
                ):
                    summary_text = rotation_summary_value
                rotation_window = metrics_block.get("rotation_window")
                if isinstance(rotation_window, Mapping):
                    rotation_info["window"] = dict(rotation_window)
                credential_expiry_value = metrics_block.get(
                    "heartbeat_expiry"
                ) or metrics_block.get("credential_expiry")
                if credential_expiry_value:
                    rotation_info["credential_expiry"] = credential_expiry_value
            if summary_text is None:
                summary_candidate = stage_b_summary.get("summary")
                if isinstance(summary_candidate, str) and summary_candidate.strip():
                    summary_text = summary_candidate
            if summary_text:
                rotation_info["summary"] = summary_text
        if rotation_info:
            merged_payload["rotation"] = rotation_info

        stage_a_warns = _notes_present(stage_a_notes) or any(
            _notes_present(notes) for notes in stage_a_slug_notes.values()
        )
        stage_b_warns = _notes_present(stage_b_notes)
        stage_b_slug_entries = (
            stage_b_section.get("slugs")
            if isinstance(stage_b_section.get("slugs"), Mapping)
            else {}
        )
        for slug_entry in stage_b_slug_entries.values():
            if not isinstance(slug_entry, Mapping):
                continue
            if _notes_present(_ensure_list(slug_entry.get("risk_notes"))):
                stage_b_warns = True
                break

        if (
            stage_a_status == "success"
            and stage_b_status == "success"
            and not stage_a_warns
            and not stage_b_warns
        ):
            merged_payload["overall_status"] = "ready"
        else:
            merged_payload["overall_status"] = "requires_attention"
        return merged_payload

    merged_snapshot = _build_merged(stage_a_section, stage_b_section)

    metrics.update(
        {
            "stage_a": stage_a_section,
            "stage_b": stage_b_section,
            "merged": merged_snapshot,
        }
    )

    readiness_stage = (
        bundle_data.get("stage")
        if isinstance(bundle_data, Mapping) and bundle_data.get("stage")
        else _STAGE_C3_SLUG
    )
    readiness_snapshot = {
        "stage": readiness_stage,
        "generated_at": metrics.get("generated_at"),
        "stage_a": stage_a_section,
        "stage_b": stage_b_section,
        "merged": merged_snapshot,
        "missing": metrics.get("missing", []),
    }
    if bundle_path.exists():
        readiness_snapshot["bundle_path"] = str(bundle_path)
    if summary_path.exists():
        readiness_snapshot["summary_path"] = str(summary_path)
    payload["readiness"] = readiness_snapshot

    if bundle_data:
        bundle_data.setdefault("stage_a", stage_a_section)
        bundle_data.setdefault("stage_b", stage_b_section)
        bundle_data["merged"] = merged_snapshot
        metrics["bundle"] = bundle_data

    artifacts = payload.setdefault("artifacts", {})
    if bundle_path.exists():
        artifacts.setdefault("readiness_bundle", str(bundle_path))
    if summary_path.exists():
        artifacts.setdefault("readiness_summary", str(summary_path))

    stage_a_slug_sections = stage_a_section.get("slugs")
    if isinstance(stage_a_slug_sections, Mapping) and stage_a_slug_sections:
        for slug, slug_section in stage_a_slug_sections.items():
            if not isinstance(slug_section, Mapping):
                continue
            slug_key = str(slug).lower()
            summary_path = _preferred_artifact_path(
                slug_section.get("summary_path"),
                slug_section.get("source_summary_path"),
                f"stage_a:{slug_key} summary",
            )
            if summary_path:
                artifacts.setdefault(f"stage_a_{slug_key}_summary", summary_path)
            artifacts_list = slug_section.get("artifacts") or []
            fallback_artifacts = (
                slug_section.get("source_artifacts")
                if isinstance(slug_section.get("source_artifacts"), list)
                else []
            )
            for index, artifact_path in enumerate(artifacts_list):
                resolved_artifact = _preferred_artifact_path(
                    artifact_path,
                    (
                        fallback_artifacts[index]
                        if index < len(fallback_artifacts)
                        else None
                    ),
                    f"stage_a:{slug_key} artifact {index + 1}",
                )
                if resolved_artifact:
                    artifacts.setdefault(
                        f"stage_a_{slug_key}_artifact_{index + 1}",
                        resolved_artifact,
                    )
    else:
        summary_path = _preferred_artifact_path(
            stage_a_section.get("summary_path"),
            stage_a_section.get("source_summary_path"),
            "stage_a summary",
        )
        if summary_path:
            artifacts.setdefault("stage_a_summary", summary_path)
        fallback_artifacts = (
            stage_a_section.get("source_artifacts")
            if isinstance(stage_a_section.get("source_artifacts"), list)
            else []
        )
        for index, artifact_path in enumerate(stage_a_section.get("artifacts") or []):
            resolved_artifact = _preferred_artifact_path(
                artifact_path,
                fallback_artifacts[index] if index < len(fallback_artifacts) else None,
                f"stage_a artifact {index + 1}",
            )
            if resolved_artifact:
                artifacts.setdefault(
                    f"stage_a_artifact_{index + 1}",
                    resolved_artifact,
                )

    summary_path_b = _preferred_artifact_path(
        stage_b_section.get("summary_path"),
        stage_b_section.get("source_summary_path"),
        "stage_b summary",
    )
    if summary_path_b:
        artifacts.setdefault("stage_b_summary", summary_path_b)
    fallback_stage_b = (
        stage_b_section.get("source_artifacts")
        if isinstance(stage_b_section.get("source_artifacts"), list)
        else []
    )
    for index, artifact_path in enumerate(stage_b_section.get("artifacts") or []):
        resolved_artifact = _preferred_artifact_path(
            artifact_path,
            fallback_stage_b[index] if index < len(fallback_stage_b) else None,
            f"stage_b artifact {index + 1}",
        )
        if resolved_artifact:
            artifacts.setdefault(
                f"stage_b_artifact_{index + 1}",
                resolved_artifact,
            )

    error_messages: list[str] = []
    if metrics["missing"]:
        error_messages.append(
            "missing readiness summaries: " + ", ".join(metrics["missing"])
        )

    attention_targets = []
    if stage_a_status != "success":
        attention_targets.append("stage_a")
    if stage_b_status != "success":
        attention_targets.append("stage_b")
    if attention_targets:
        error_messages.append(
            "readiness requires_attention: " + ", ".join(attention_targets)
        )

    if error_messages:
        payload["status"] = "error"
        payload["error"] = "; ".join(error_messages)
    elif merged_snapshot.get("overall_status") == "requires_attention":
        attention_reasons: list[str] = []
        if stage_a_has_risk:
            attention_reasons.append("stage_a risk notes present")
        if stage_b_has_risk:
            attention_reasons.append("stage_b risk notes present")
        if not attention_reasons:
            attention_reasons.append("upstream readiness warnings present")
        payload["status"] = "error"
        payload["error"] = "readiness requires_attention: " + ", ".join(
            attention_reasons
        )

    return metrics


async def _stage_c4_metrics(
    _stdout_text: str,
    _stderr_text: str,
    log_dir: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        await _ensure_mcp_ready_for_request()
    except HTTPException as exc:  # pragma: no cover - handled in tests
        payload["status"] = "error"
        payload["error"] = str(exc.detail)
        return {
            "handshake": None,
            "heartbeat_active": False,
            "error": exc.detail,
        }

    handshake_path = log_dir / "mcp_handshake.json"
    heartbeat_path = log_dir / "heartbeat.json"

    artifacts = payload.setdefault("artifacts", {})
    if handshake_path.exists():
        artifacts.setdefault("mcp_handshake", str(handshake_path))
    if heartbeat_path.exists():
        artifacts.setdefault("heartbeat", str(heartbeat_path))

    handshake_data: Mapping[str, Any] | None = None
    handshake_error: str | None = None
    try:
        handshake_data = json.loads(handshake_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        handshake_error = f"missing handshake artifact: {handshake_path}"
    except json.JSONDecodeError as exc:
        handshake_error = f"invalid handshake artifact: {exc}"

    heartbeat_data: Mapping[str, Any] | None = None
    heartbeat_error: str | None = None
    heartbeat_payload: Any = None
    credential_expiry: Any = None
    try:
        heartbeat_data = json.loads(heartbeat_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        heartbeat_error = f"missing heartbeat artifact: {heartbeat_path}"
    except json.JSONDecodeError as exc:
        heartbeat_error = f"invalid heartbeat artifact: {exc}"
    else:
        heartbeat_payload = heartbeat_data.get("payload")
        credential_expiry = heartbeat_data.get("credential_expiry")

    heartbeat_payload_path = log_dir / "heartbeat_payload.json"
    if heartbeat_payload is not None and heartbeat_error is None:
        try:
            heartbeat_payload_path.write_text(
                json.dumps(heartbeat_payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            heartbeat_error = f"failed to persist heartbeat payload: {exc}"
        else:
            artifacts.setdefault("heartbeat_payload", str(heartbeat_payload_path))

    heartbeat_emitted = bool(heartbeat_payload)

    rotation_log_path = _REPO_ROOT / "logs" / "stage_b_rotation_drills.jsonl"
    rotation_metadata_path = log_dir / "rotation_metadata.json"
    rotation_entries: list[Mapping[str, Any]] = []
    rotation_entry: Mapping[str, Any] | None = None
    rotation_error: str | None = None
    ledger_window_id: str | None = None

    try:
        if rotation_log_path.exists():
            for line in rotation_log_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rotation_entries.append(json.loads(line))
        else:
            rotation_error = f"rotation drill ledger missing: {rotation_log_path}"
    except OSError as exc:
        rotation_error = f"failed to read rotation drill ledger: {exc}"
    except json.JSONDecodeError as exc:
        rotation_error = f"invalid rotation drill ledger: {exc}"

    if not rotation_error:
        if rotation_entries:
            rotation_entry = rotation_entries[-1]
            rotation_window = rotation_entry.get("rotation_window")
            if isinstance(rotation_window, Mapping):
                window_id_value = rotation_window.get("window_id")
                if isinstance(window_id_value, str) and window_id_value.strip():
                    ledger_window_id = window_id_value
                else:
                    rotation_error = (
                        "latest rotation drill missing rotation_window.window_id"
                    )
            else:
                rotation_error = (
                    "latest rotation drill missing rotation_window metadata"
                )
        else:
            rotation_error = "rotation drill ledger empty"

    handshake_rotation: Mapping[str, Any] | None = None
    if isinstance(handshake_data, Mapping):
        candidate_rotation = handshake_data.get("rotation")
        if isinstance(candidate_rotation, Mapping):
            handshake_rotation = candidate_rotation
        else:
            echo_section = handshake_data.get("echo")
            if isinstance(echo_section, Mapping):
                echo_rotation = echo_section.get("rotation")
                if isinstance(echo_rotation, Mapping):
                    handshake_rotation = echo_rotation

    handshake_window_id: str | None = None
    if handshake_rotation is not None:
        window_candidate = handshake_rotation.get("window_id")
        if isinstance(window_candidate, str) and window_candidate.strip():
            handshake_window_id = window_candidate

    credential_window_payload: Mapping[str, Any] | None = None
    if isinstance(rotation_entry, Mapping):
        candidate_window = rotation_entry.get("credential_window")
        if isinstance(candidate_window, Mapping):
            credential_window_payload = candidate_window

    credential_window_path = log_dir / "credential_window.json"

    if rotation_entry is not None and rotation_error is None:
        try:
            rotation_metadata_path.write_text(
                json.dumps(rotation_entry, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            rotation_error = f"failed to persist rotation metadata: {exc}"
        else:
            artifacts.setdefault("rotation_metadata", str(rotation_metadata_path))
        if credential_window_payload is not None and rotation_error is None:
            try:
                credential_window_path.write_text(
                    json.dumps(credential_window_payload, indent=2),
                    encoding="utf-8",
                )
            except OSError as exc:
                rotation_error = f"failed to persist credential window: {exc}"
            else:
                artifacts.setdefault("credential_window", str(credential_window_path))

    rotation_verified = bool(
        ledger_window_id
        and handshake_window_id
        and ledger_window_id == handshake_window_id
    )
    if not rotation_error and not rotation_verified:
        if ledger_window_id and handshake_window_id:
            rotation_error = (
                "rotation window mismatch: "
                f"handshake={handshake_window_id} ledger={ledger_window_id}"
            )
        elif ledger_window_id:
            rotation_error = "handshake rotation window missing"
        elif handshake_window_id:
            rotation_error = "rotation ledger window missing"

    metrics: dict[str, Any] = {
        "handshake": _sanitize_for_json(handshake_data),
        "credential_expiry": _sanitize_for_json(credential_expiry),
        "heartbeat_active": bool(
            _MCP_HEARTBEAT_TASK is not None and not _MCP_HEARTBEAT_TASK.done()
        ),
        "heartbeat_emitted": heartbeat_emitted,
        "rotation_window_hours": ROTATION_WINDOW_HOURS,
    }
    if heartbeat_payload is not None:
        metrics["heartbeat_payload"] = _sanitize_for_json(heartbeat_payload)
    if credential_window_payload is not None:
        metrics["credential_window"] = _sanitize_for_json(credential_window_payload)
    if rotation_entry is not None:
        metrics["rotation_metadata"] = _sanitize_for_json(rotation_entry)
    if ledger_window_id:
        metrics["ledger_window_id"] = ledger_window_id
    if handshake_window_id:
        metrics["rotation_window_id"] = handshake_window_id
    elif ledger_window_id:
        metrics["rotation_window_id"] = ledger_window_id
    metrics["rotation_window_verified"] = rotation_verified
    if handshake_error:
        metrics["handshake_error"] = handshake_error
    if heartbeat_error:
        metrics["heartbeat_error"] = heartbeat_error
    if rotation_error:
        metrics["rotation_error"] = rotation_error

    if "credential_window" in metrics:
        payload["credential_window"] = metrics["credential_window"]

    if handshake_error or heartbeat_error or rotation_error:
        payload["status"] = "error"
        payload["error"] = "; ".join(
            message
            for message in (handshake_error, heartbeat_error, rotation_error)
            if message
        )

    return metrics


def _format_diff_path(segments: Sequence[str]) -> str:
    """Return a human-readable dotted path for diff segments."""

    if not segments:
        return "<root>"

    parts: list[str] = []
    for segment in segments:
        if not segment:
            continue
        if segment.startswith("["):
            if parts:
                parts[-1] = parts[-1] + segment
            else:
                parts.append(segment)
        else:
            parts.append(segment)

    if not parts:
        return "<root>"

    formatted = parts[0]
    for token in parts[1:]:
        if token.startswith("["):
            formatted += token
        else:
            formatted += f".{token}"
    return formatted


def _diff_handshake_payloads(
    rest_payload: Mapping[str, Any],
    grpc_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return structural differences between REST and gRPC handshake payloads."""

    differences: list[dict[str, Any]] = []

    def _compare(path: list[str], left: Any, right: Any) -> None:
        if isinstance(left, Mapping) and isinstance(right, Mapping):
            keys = sorted(
                {str(key) for key in left.keys()} | {str(key) for key in right.keys()}
            )
            for key in keys:
                left_has = key in left
                right_has = key in right
                next_path = path + [key]
                if left_has and right_has:
                    _compare(next_path, left[key], right[key])  # type: ignore[index]
                elif left_has:
                    differences.append(
                        {
                            "path": _format_diff_path(next_path),
                            "rest": _sanitize_for_json(left[key]),
                            "grpc": None,
                        }
                    )
                else:
                    differences.append(
                        {
                            "path": _format_diff_path(next_path),
                            "rest": None,
                            "grpc": _sanitize_for_json(right[key]),
                        }
                    )
            return

        if isinstance(left, list) and isinstance(right, list):
            max_len = max(len(left), len(right))
            for index in range(max_len):
                token = f"[{index}]"
                next_path = path + [token]
                if index >= len(left):
                    differences.append(
                        {
                            "path": _format_diff_path(next_path),
                            "rest": None,
                            "grpc": _sanitize_for_json(right[index]),
                        }
                    )
                elif index >= len(right):
                    differences.append(
                        {
                            "path": _format_diff_path(next_path),
                            "rest": _sanitize_for_json(left[index]),
                            "grpc": None,
                        }
                    )
                else:
                    _compare(next_path, left[index], right[index])
            return

        if left != right:
            differences.append(
                {
                    "path": _format_diff_path(path),
                    "rest": _sanitize_for_json(left),
                    "grpc": _sanitize_for_json(right),
                }
            )

    _compare([], rest_payload, grpc_payload)
    return differences


def _extract_latency_metric(trace: Mapping[str, Any] | None) -> float | None:
    """Return a latency metric from ``trace`` when present."""

    if not isinstance(trace, Mapping):
        return None

    for key in ("latency_ms", "duration_ms", "elapsed_ms", "latency"):
        value = trace.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue

    metrics_section = trace.get("metrics")
    if isinstance(metrics_section, Mapping):
        for key in ("latency_ms", "duration_ms", "elapsed_ms"):
            value = metrics_section.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    continue

    return None


def _publish_stage_e_transport_snapshot(
    payload: Mapping[str, Any],
    rest_attachment_path: Path,
    grpc_attachment_path: Path,
    diff_attachment_path: Path,
) -> None:
    """Write a Stage E transport snapshot under ``logs/stage_e``."""

    generated_at = datetime.now(timezone.utc)
    stage_e_run_id = (
        f"{generated_at.strftime('%Y%m%dT%H%M%SZ')}-stage_e_transport_readiness"
    )
    log_dir = _STAGE_E_ROOT / stage_e_run_id
    log_dir.mkdir(parents=True, exist_ok=True)

    def _load_json_or_default(path: Path) -> Mapping[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    diff_payload = _load_json_or_default(diff_attachment_path)

    summary_section = payload.get("summary")
    metrics_section = payload.get("metrics")
    if not isinstance(summary_section, Mapping):
        summary_section = {}
    if not isinstance(metrics_section, Mapping):
        metrics_section = {}

    heartbeat_payload: Mapping[str, Any] | None = None
    heartbeat_payload_candidate = metrics_section.get("heartbeat_payload")
    if isinstance(heartbeat_payload_candidate, Mapping):
        heartbeat_payload = heartbeat_payload_candidate
    else:
        summary_heartbeat = summary_section.get("heartbeat_payload")
        if isinstance(summary_heartbeat, Mapping):
            heartbeat_payload = summary_heartbeat

    heartbeat_emitted = bool(metrics_section.get("heartbeat_emitted")) or bool(
        summary_section.get("heartbeat_emitted")
    )

    source_summary_path = payload.get("summary_path")
    stage_c_run_id = str(
        payload.get("run_id") or summary_section.get("run_id") or "unknown-stage-c4"
    )

    connectors: dict[str, Any] = {}
    missing_connectors: list[str] = []
    parity_failures: list[str] = []
    heartbeat_gaps: list[str] = []
    telemetry_hashes: dict[str, dict[str, str | None]] = {}
    environment_notes: set[str] = set()

    for connector_id in _STAGE_E_CONNECTORS:
        connector_dir = log_dir / connector_id
        connector_dir.mkdir(parents=True, exist_ok=True)
        connector_summary: dict[str, Any] = {
            "connector_id": connector_id,
            "rotation_window": None,
            "rotated_at": None,
            "parity": False,
            "checksum_match": False,
            "rest_checksum": None,
            "grpc_checksum": None,
            "latency_ms": {"rest": None, "grpc": None},
            "monitoring_gaps": [],
            "artifacts": {},
        }

        entry = latest_rotation_entry(connector_id)
        if not isinstance(entry, Mapping):
            missing_connectors.append(connector_id)
            telemetry_hashes[connector_id] = {"rest": None, "grpc": None}
            connector_summary["status"] = "missing_rotation_entry"
            connector_summary["monitoring_gaps"] = [
                "rest_latency_missing",
                "grpc_latency_missing",
                "heartbeat_missing",
                "heartbeat_latency_missing",
            ]
            heartbeat_gaps.append(connector_id)
            connectors[connector_id] = connector_summary
            environment_notes.add(
                "environment-limited: rotation ledger missing connector parity traces"
            )
            continue

        connector_summary["rotated_at"] = entry.get("rotated_at")
        rotation_window = entry.get("rotation_window")
        if isinstance(rotation_window, Mapping):
            connector_summary["rotation_window"] = rotation_window

        traces = entry.get("traces")
        if not isinstance(traces, Mapping):
            traces = None
        rest_trace = None
        grpc_trace = None
        if isinstance(traces, Mapping):
            rest_candidate = traces.get("rest")
            grpc_candidate = traces.get("grpc")
            if isinstance(rest_candidate, Mapping):
                rest_trace = rest_candidate
            if isinstance(grpc_candidate, Mapping):
                grpc_trace = grpc_candidate

        rest_handshake_raw: Mapping[str, Any] | None = None
        grpc_handshake_raw: Mapping[str, Any] | None = None
        if isinstance(rest_trace, Mapping):
            if isinstance(rest_trace.get("normalized"), Mapping):
                rest_handshake_raw = rest_trace["normalized"]  # type: ignore[index]
            elif isinstance(rest_trace.get("handshake"), Mapping):
                rest_handshake_raw = rest_trace["handshake"]  # type: ignore[index]
            else:
                response_section = rest_trace.get("response")
                if isinstance(response_section, Mapping):
                    candidate = response_section.get("handshake")
                    if isinstance(candidate, Mapping):
                        rest_handshake_raw = candidate

        if isinstance(grpc_trace, Mapping):
            if isinstance(grpc_trace.get("handshake_equivalent"), Mapping):
                grpc_handshake_raw = grpc_trace["handshake_equivalent"]  # type: ignore[index]
            else:
                response_section = grpc_trace.get("response")
                if isinstance(response_section, Mapping):
                    candidate = response_section.get("handshake_equivalent")
                    if isinstance(candidate, Mapping):
                        grpc_handshake_raw = candidate
                    elif isinstance(response_section.get("handshake"), Mapping):
                        grpc_handshake_raw = response_section["handshake"]  # type: ignore[index]

        rest_normalized = normalize_handshake_for_trace(rest_handshake_raw)
        grpc_normalized = normalize_handshake_for_trace(grpc_handshake_raw)

        rest_checksum = None
        if isinstance(rest_trace, Mapping):
            checksum_candidate = rest_trace.get("checksum")
            if isinstance(checksum_candidate, str):
                rest_checksum = checksum_candidate
        if rest_checksum is None:
            rest_checksum = compute_handshake_checksum(rest_handshake_raw)

        grpc_checksum = None
        grpc_metadata = None
        if isinstance(grpc_trace, Mapping):
            checksum_candidate = grpc_trace.get("checksum")
            if isinstance(checksum_candidate, str):
                grpc_checksum = checksum_candidate
            metadata_candidate = grpc_trace.get("metadata")
            if isinstance(metadata_candidate, Mapping):
                grpc_metadata = metadata_candidate
                parity_checksum = metadata_candidate.get("parity_checksum")
                if isinstance(parity_checksum, str):
                    grpc_checksum = parity_checksum
        if grpc_checksum is None:
            grpc_checksum = compute_handshake_checksum(grpc_handshake_raw)

        telemetry_hashes[connector_id] = {
            "rest": rest_checksum,
            "grpc": grpc_checksum,
        }

        parity = bool(
            rest_normalized and grpc_normalized and rest_normalized == grpc_normalized
        )
        connector_summary["parity"] = parity
        connector_summary["rest_checksum"] = rest_checksum
        connector_summary["grpc_checksum"] = grpc_checksum
        checksum_match = bool(
            rest_checksum and grpc_checksum and rest_checksum == grpc_checksum
        )
        connector_summary["checksum_match"] = checksum_match

        differences: list[dict[str, Any]] = []
        if parity:
            differences = []
        elif rest_normalized and grpc_normalized:
            differences = _diff_handshake_payloads(rest_normalized, grpc_normalized)
        connector_summary["differences"] = differences
        if not parity or not checksum_match:
            parity_failures.append(connector_id)

        rest_latency = _extract_latency_metric(rest_trace)
        grpc_latency = _extract_latency_metric(grpc_trace)
        connector_summary["latency_ms"] = {"rest": rest_latency, "grpc": grpc_latency}
        monitoring_gaps = connector_summary["monitoring_gaps"]
        if rest_latency is None:
            monitoring_gaps.append("rest_latency_missing")
        if grpc_latency is None:
            monitoring_gaps.append("grpc_latency_missing")
        if rest_latency is None or grpc_latency is None:
            environment_notes.add(
                "environment-limited: transport latency metrics unavailable "
                "in sandbox traces"
            )

        heartbeat_latency_ms: float | None = None
        heartbeat_emitted_for_connector = False
        if connector_id == "operator_api":
            heartbeat_emitted_for_connector = heartbeat_emitted
            if not heartbeat_emitted_for_connector:
                monitoring_gaps.append("heartbeat_missing")
            if heartbeat_payload is None:
                environment_notes.add(
                    "environment-limited: heartbeat payload unavailable for "
                    "operator_api"
                )
            else:
                heartbeat_path = connector_dir / "heartbeat_payload.json"
                heartbeat_path.write_text(
                    json.dumps(
                        _sanitize_for_json(heartbeat_payload),
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                connector_summary["heartbeat_payload"] = str(heartbeat_path)
        else:
            monitoring_gaps.append("heartbeat_missing")
            heartbeat_emitted_for_connector = False
            environment_notes.add(
                "environment-limited: connector heartbeat instrumentation pending"
            )

        connector_summary["heartbeat_emitted"] = heartbeat_emitted_for_connector
        connector_summary["heartbeat_latency_ms"] = heartbeat_latency_ms
        monitoring_gaps.append("heartbeat_latency_missing")
        if not heartbeat_emitted_for_connector:
            heartbeat_gaps.append(connector_id)

        diff_rotation_window = None
        if connector_id == "operator_api" and isinstance(diff_payload, Mapping):
            diff_rotation_candidate = diff_payload.get("rotation_window")
            if isinstance(diff_rotation_candidate, Mapping):
                diff_rotation_window = diff_rotation_candidate
        if not isinstance(diff_rotation_window, Mapping) and isinstance(
            grpc_metadata, Mapping
        ):
            diff_rotation_window = grpc_metadata.get("rotation_window")

        artifacts = connector_summary["artifacts"]
        rest_trace_path = connector_dir / "rest_trace.json"
        rest_trace_path.write_text(
            json.dumps(
                _sanitize_for_json(
                    {
                        "protocol": "REST",
                        "trace": rest_trace,
                        "normalized": rest_normalized,
                        "checksum": rest_checksum,
                    }
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        artifacts["rest"] = str(rest_trace_path)

        grpc_trace_path = connector_dir / "grpc_trace.json"
        grpc_trace_path.write_text(
            json.dumps(
                _sanitize_for_json(
                    {
                        "protocol": "gRPC",
                        "trace": grpc_trace,
                        "handshake_equivalent": grpc_handshake_raw,
                        "metadata": grpc_metadata,
                        "checksum": grpc_checksum,
                    }
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        artifacts["grpc"] = str(grpc_trace_path)

        diff_trace_path = connector_dir / "rest_grpc_diff.json"
        diff_trace_payload = {
            "parity": parity,
            "differences": differences,
            "rest_checksum": rest_checksum,
            "grpc_checksum": grpc_checksum,
            "checksum_match": checksum_match,
            "rotation_window": diff_rotation_window,
        }
        diff_trace_path.write_text(
            json.dumps(
                _sanitize_for_json(diff_trace_payload),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        artifacts["diff"] = str(diff_trace_path)

        connectors[connector_id] = connector_summary

    status = "warning"
    if missing_connectors:
        status = "requires_attention"
    elif parity_failures:
        status = "requires_attention"

    summary_payload = {
        "status": status,
        "stage": "stage_e_transport_readiness",
        "run_id": stage_e_run_id,
        "generated_at": generated_at.isoformat(),
        "dashboard": {
            "url": _STAGE_E_DASHBOARD_URL,
            "updated_at": generated_at.isoformat(),
        },
        "source_stage_c": {
            "run_id": stage_c_run_id,
            "summary_path": source_summary_path,
            "artifacts": {
                "rest": str(rest_attachment_path),
                "grpc": str(grpc_attachment_path),
                "diff": str(diff_attachment_path),
            },
        },
        "connectors": connectors,
        "missing_connectors": missing_connectors,
        "parity_failures": parity_failures,
        "heartbeat_gaps": heartbeat_gaps,
        "telemetry_hashes": telemetry_hashes,
    }

    if environment_notes:
        summary_payload["environment_notes"] = sorted(environment_notes)

    summary_path = log_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            _sanitize_for_json(summary_payload),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    if isinstance(payload, dict):
        stage_e_section = payload.setdefault("stage_e", {})
        if isinstance(stage_e_section, dict):
            stage_e_section.update(
                {
                    "run_id": stage_e_run_id,
                    "summary_path": str(summary_path),
                    "status": status,
                    "heartbeat_gaps": heartbeat_gaps,
                }
            )
        artifacts_section = payload.setdefault("artifacts", {})
        if isinstance(artifacts_section, dict):
            artifacts_section.setdefault("stage_e_snapshot", str(summary_path))


def _attach_rest_grpc_parity(payload: dict[str, Any]) -> None:
    """Persist REST and gRPC handshake parity attachments for Stage C4 runs."""

    log_dir_raw = payload.get("log_dir")
    if not isinstance(log_dir_raw, str) or not log_dir_raw:
        raise ValueError("stage C4 drill payload missing log directory")
    log_dir = Path(log_dir_raw)

    summary = payload.get("summary")
    summary_dict = dict(summary) if isinstance(summary, Mapping) else {}

    handshake_path_raw = summary_dict.get("handshake_path") if summary_dict else None
    if isinstance(handshake_path_raw, str) and handshake_path_raw:
        handshake_path = Path(handshake_path_raw)
    else:
        handshake_path = log_dir / "mcp_handshake.json"

    try:
        handshake_data = json.loads(handshake_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"missing handshake artifact: {handshake_path}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"invalid handshake artifact: {exc}") from exc

    normalized_rest = normalize_handshake_for_trace(handshake_data)
    rest_checksum = compute_handshake_checksum(handshake_data)

    rotation_entry = latest_rotation_entry("operator_api")
    if rotation_entry is None:
        raise ValueError("rotation ledger missing operator_api entry for parity diff")
    traces = rotation_entry.get("traces")
    if not isinstance(traces, Mapping):
        raise ValueError("rotation ledger entry missing trace captures")
    grpc_trace = traces.get("grpc")
    if not isinstance(grpc_trace, Mapping):
        raise ValueError("rotation ledger entry missing gRPC trial trace")

    grpc_response = grpc_trace.get("response")
    handshake_equivalent: Mapping[str, Any] = {}
    if isinstance(grpc_response, Mapping):
        candidate = grpc_response.get("handshake_equivalent")
        if isinstance(candidate, Mapping):
            handshake_equivalent = candidate

    metadata = grpc_trace.get("metadata")
    if not isinstance(metadata, Mapping):
        metadata = {}
    grpc_checksum = metadata.get("parity_checksum")

    parity = normalized_rest == handshake_equivalent
    differences = (
        []
        if parity
        else _diff_handshake_payloads(normalized_rest, handshake_equivalent)
    )
    checksum_match = bool(
        rest_checksum and grpc_checksum and rest_checksum == grpc_checksum
    )

    diff_payload = {
        "parity": parity,
        "differences": differences,
        "rest_checksum": rest_checksum,
        "grpc_checksum": grpc_checksum,
        "checksum_match": checksum_match,
        "rotation_window": metadata.get("rotation_window"),
    }

    rest_session = normalized_rest.get("session")
    rest_expiry = (
        rest_session.get("credential_expiry")
        if isinstance(rest_session, Mapping)
        else None
    )

    rest_attachment = {
        "protocol": "REST",
        "handshake": handshake_data,
        "normalized": normalized_rest,
        "credential_expiry": rest_expiry,
        "checksum": rest_checksum,
    }

    grpc_attachment = {
        "protocol": "gRPC",
        "trace": grpc_trace,
        "handshake_equivalent": handshake_equivalent,
        "ledger_connector_id": rotation_entry.get("connector_id"),
        "ledger_rotated_at": rotation_entry.get("rotated_at"),
        "credential_expiry": metadata.get("credential_expiry"),
        "checksum": grpc_checksum,
    }

    rest_path = log_dir / "rest_handshake_with_expiry.json"
    grpc_path = log_dir / "grpc_trial_handshake.json"
    diff_path = log_dir / "rest_grpc_handshake_diff.json"

    rest_path.write_text(
        json.dumps(rest_attachment, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    grpc_path.write_text(
        json.dumps(grpc_attachment, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    diff_path.write_text(
        json.dumps(diff_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    artifacts = payload.setdefault("artifacts", {})
    artifacts.setdefault("rest_handshake_with_expiry", str(rest_path))
    artifacts.setdefault("grpc_trial_handshake", str(grpc_path))
    artifacts.setdefault("rest_grpc_diff", str(diff_path))

    metrics = payload.get("metrics")
    if isinstance(metrics, dict):
        metrics["rest_grpc_parity"] = parity
        metrics["rest_grpc_checksum_match"] = checksum_match
        if differences:
            metrics["rest_grpc_differences"] = differences

    attachments = {
        "rest": str(rest_path),
        "grpc": str(grpc_path),
        "diff": str(diff_path),
    }

    payload["handshake_artifacts"] = attachments
    payload["handshake_parity"] = diff_payload

    summary_dict["rest_handshake_with_expiry"] = str(rest_path)
    summary_dict["grpc_trial_handshake"] = str(grpc_path)
    summary_dict["rest_grpc_diff"] = str(diff_path)
    summary_dict["rest_grpc_parity"] = parity
    summary_dict["rest_checksum"] = rest_checksum
    summary_dict["grpc_checksum"] = grpc_checksum
    payload["summary"] = summary_dict

    summary_path_raw = payload.get("summary_path")
    if isinstance(summary_path_raw, str) and summary_path_raw:
        summary_path = Path(summary_path_raw)
        try:
            summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):  # pragma: no cover - defensive guard
            summary_payload = {}
        summary_payload["summary"] = summary_dict
        summary_payload["handshake_artifacts"] = attachments
        summary_payload["handshake_parity"] = diff_payload
        summary_path.write_text(
            json.dumps(summary_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    try:
        _publish_stage_e_transport_snapshot(
            payload,
            rest_path,
            grpc_path,
            diff_path,
        )
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("failed to publish Stage E transport snapshot")
        if isinstance(payload, dict):
            warnings = payload.setdefault("warnings", [])
            if isinstance(warnings, list):
                warnings.append("stage_e_transport_snapshot_failed")


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
    path = _REPO_ROOT / "logs" / "operator_commands.jsonl"
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


async def execute_command_for_transport(
    data: Mapping[str, str],
    *,
    transport: str,
    fallback: bool = False,
) -> dict[str, object]:
    """Execute the operator command using shared transport-aware logic."""

    payload = dict(data) if isinstance(data, Mapping) else {}
    operator = str(payload.get("operator", ""))
    agent = str(payload.get("agent", ""))
    command_name = str(payload.get("command", ""))

    start = time.perf_counter()
    if not operator or not agent or not command_name:
        _record_error("dispatch_command", transport, "validation")
        _record_latency(
            "dispatch_command", transport, (time.perf_counter() - start) * 1000.0
        )
        raise CommandValidationError("operator, agent and command required")

    attributes = {
        "transport": transport,
        "operator": operator,
        "agent": agent,
        "command": command_name,
    }

    with _tracer.start_as_current_span(
        "operator_api.dispatch_command", attributes=attributes
    ) as span:
        span.set_attribute("operator_api.transport.fallback", fallback)
        if fallback:
            span.add_event("fallback-engaged", {"transport": transport})
            logger.info(
                "operator_api %s fallback engaged for %s→%s",
                transport,
                operator,
                agent,
            )

        try:
            try:
                await _ensure_mcp_ready_for_request()
            except HTTPException as exc:
                detail = str(exc.detail)
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, detail))
                _record_error("dispatch_command", transport, "handshake")
                raise MCPHandshakeError(exc.status_code, detail) from exc

            command_id = str(uuid4())
            span.set_attribute("operator_api.command_id", command_id)
            started_at = datetime.utcnow().isoformat()

            def _noop() -> dict[str, str]:
                return {"ack": command_name}

            await broadcast_event(
                {
                    "event": "ack",
                    "command": command_name,
                    "command_id": command_id,
                }
            )
            span.add_event("command-ack", {"command_id": command_id})

            try:
                result = _dispatcher.dispatch(
                    operator, agent, _noop, command_id=command_id
                )
            except PermissionError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                _record_error("dispatch_command", transport, "permission")
                raise
            except Exception as exc:  # pragma: no cover - dispatcher failure
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, "dispatch failed"))
                logger.error("dispatch failed: %s", exc)
                _record_error("dispatch_command", transport, "exception")
                raise CommandDispatchError("dispatch failed") from exc

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
            span.add_event(
                "command-progress", {"command_id": command_id, "percent": 100}
            )
            span.set_status(Status(StatusCode.OK))

            response = {"command_id": command_id, "result": result}
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            _record_latency("dispatch_command", transport, duration_ms)
            if fallback:
                _record_fallback("dispatch_command", transport)


def execute_memory_query_for_transport(
    query: str,
    *,
    transport: str,
    fallback: bool = False,
) -> dict[str, object]:
    """Execute a memory query for the given ``transport``."""

    start = time.perf_counter()
    attributes = {"transport": transport, "fallback": fallback}
    with _tracer.start_as_current_span(
        "operator_api.memory_query", attributes=attributes
    ) as span:
        if fallback:
            span.add_event("fallback-engaged", {"transport": transport})
            logger.info("operator_api %s memory fallback engaged", transport)

        try:
            results = query_memory(query)
            span.set_status(Status(StatusCode.OK))
            return {"results": results}
        except Exception as exc:  # pragma: no cover - defensive logging
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            _record_error("memory_query", transport, "exception")
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            _record_latency("memory_query", transport, duration_ms)
            if fallback:
                _record_fallback("memory_query", transport)


def execute_handover_for_transport(
    payload: Mapping[str, str] | None,
    *,
    transport: str,
    fallback: bool = False,
) -> dict[str, object]:
    """Execute the handover flow and emit telemetry attributes."""

    data = dict(payload or {})
    component = str(data.get("component", "unknown"))
    error = str(data.get("error", "operator initiated"))

    start = time.perf_counter()
    attributes = {
        "transport": transport,
        "component": component,
        "fallback": fallback,
    }
    with _tracer.start_as_current_span(
        "operator_api.handover", attributes=attributes
    ) as span:
        if fallback:
            span.add_event("fallback-engaged", {"transport": transport})
            logger.info(
                "operator_api %s handover fallback engaged for %s",
                transport,
                component,
            )

        try:
            result = ai_invoker.handover(component, error)
            span.set_status(Status(StatusCode.OK))
            return {"handover": result}
        except Exception as exc:  # pragma: no cover - defensive logging
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            _record_error("handover", transport, "exception")
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            _record_latency("handover", transport, duration_ms)
            if fallback:
                _record_fallback("handover", transport)


@router.post("/operator/command")
async def dispatch_command(data: dict[str, str]) -> dict[str, object]:
    """Dispatch an operator command to a target agent."""
    try:
        return await execute_command_for_transport(data, transport="rest")
    except CommandValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MCPHandshakeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except CommandDispatchError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/start_ignition")
async def start_ignition() -> dict[str, str]:
    """Kick off ignition via ``boot_orchestrator.start``."""

    boot_orchestrator.start()  # type: ignore[attr-defined]
    return {"status": "started"}


@router.post("/memory/query")
async def memory_query_endpoint(payload: dict[str, str]) -> dict[str, object]:
    """Return aggregated memory search results via :func:`query_memory`."""

    query = payload.get("query", "")
    return execute_memory_query_for_transport(query, transport="rest")


@router.post("/handover")
async def handover_endpoint(payload: dict[str, str] | None = None) -> dict[str, object]:
    """Escalate failure context to AI handover."""

    return execute_handover_for_transport(payload, transport="rest")


@router.post("/alpha/stage-a1-boot-telemetry")
async def stage_a1_boot_telemetry() -> dict[str, Any]:
    """Execute the bootstrap telemetry sweep and archive logs under ``logs/stage_a``."""

    command = [sys.executable, str(_SCRIPTS_DIR / "bootstrap.py")]
    result = await _run_stage_workflow(
        _STAGE_A_ROOT, "stage_a1_boot_telemetry", command
    )
    return _attach_summary_artifacts(result)


@router.post("/alpha/stage-a2-crown-replays")
async def stage_a2_crown_replays() -> dict[str, Any]:
    """Capture Crown replay evidence for Stage A auditing."""

    command = [sys.executable, str(_SCRIPTS_DIR / "crown_capture_replays.py")]
    result = await _run_stage_workflow(_STAGE_A_ROOT, "stage_a2_crown_replays", command)
    return _attach_summary_artifacts(result)


@router.post("/alpha/stage-a3-gate-shakeout")
async def stage_a3_gate_shakeout() -> dict[str, Any]:
    """Run the Alpha gate automation shakeout script."""

    command = ["bash", str(_SCRIPTS_DIR / "run_alpha_gate.sh"), "--sandbox"]
    result = await _run_stage_workflow(_STAGE_A_ROOT, "stage_a3_gate_shakeout", command)

    summary = result.get("summary")
    summary_warnings: Sequence[Any] | None = None
    if isinstance(summary, Mapping):
        warnings = summary.get("warnings")
        if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)):
            summary_warnings = list(warnings)

    top_level_warnings = result.get("warnings")
    if isinstance(top_level_warnings, Sequence) and not isinstance(
        top_level_warnings, (str, bytes)
    ):
        summary_warnings = list(top_level_warnings)

    if summary_warnings:
        result["warnings"] = summary_warnings
        result["sandbox_warnings"] = summary_warnings

    return _attach_summary_artifacts(result)


@router.post("/alpha/stage-b1-memory-proof")
async def stage_b1_memory_proof() -> dict[str, Any]:
    """Execute the Stage B memory load proof and summarise latency metrics."""

    command = [
        sys.executable,
        str(_SCRIPTS_DIR / "memory_load_proof.py"),
        "data/vector_memory_scaling/corpus.jsonl",
        "--limit",
        "1000",
    ]
    result = await _run_stage_workflow(
        _STAGE_B_ROOT,
        "stage_b1_memory_proof",
        command,
        metrics_extractor=_stage_b1_metrics,
    )
    result = _attach_summary_artifacts(result)
    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Stage B1 memory proof failed"),
        )
    return result


@router.post("/alpha/stage-b2-sonic-rehearsal")
async def stage_b2_sonic_rehearsal() -> dict[str, Any]:
    """Capture the Stage B sonic rehearsal connector packet for review."""

    command = [
        sys.executable,
        str(_SCRIPTS_DIR / "generate_stage_b_rehearsal_packet.py"),
    ]
    result = await _run_stage_workflow(
        _STAGE_B_ROOT,
        "stage_b2_sonic_rehearsal",
        command,
        metrics_extractor=_stage_b2_metrics,
    )
    result = _attach_summary_artifacts(result)
    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Stage B2 sonic rehearsal failed"),
        )
    return result


@router.post("/alpha/stage-b3-connector-rotation")
async def stage_b3_connector_rotation() -> dict[str, Any]:
    """Run the Stage B connector rotation drill and surface handshake evidence."""

    command = [
        sys.executable,
        str(_SCRIPTS_DIR / "stage_b_smoke.py"),
        "--json",
    ]
    result = await _run_stage_workflow(
        _STAGE_B_ROOT,
        "stage_b3_connector_rotation",
        command,
        metrics_extractor=_stage_b3_metrics,
    )
    result = _attach_summary_artifacts(result)
    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Stage B3 connector rotation failed"),
        )
    return result


def _stage_c2_command(log_dir: Path) -> Sequence[str]:
    output_dir = log_dir / "demo_storyline"
    return [
        sys.executable,
        str(_SCRIPTS_DIR / "stage_c_scripted_demo.py"),
        str(output_dir),
        "--seed",
        "42",
    ]


def _stage_c3_command(log_dir: Path) -> Sequence[str]:
    from scripts import aggregate_stage_readiness as readiness_aggregate

    summary_path = log_dir / readiness_aggregate.SUMMARY_FILENAME
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    try:
        _bundle_path, summary_payload = readiness_aggregate.aggregate(log_dir)
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("stage readiness aggregation crashed: %s", exc)
        fallback_payload = {
            "status": "error",
            "stage": _STAGE_C3_SLUG,
            "generated_at": generated_at,
            "error": f"stage readiness aggregation failed: {exc}",
        }
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(fallback_payload, indent=2), encoding="utf-8"
        )
    else:
        if not summary_path.exists():
            summary_path.write_text(
                json.dumps(summary_payload, indent=2), encoding="utf-8"
            )

    runner = (
        "import json, pathlib, sys; "
        "path = pathlib.Path(sys.argv[1]); "
        "data = json.loads(path.read_text(encoding='utf-8')); "
        "print(json.dumps(data)); "
        "sys.exit(0 if data.get('status') == 'success' else 1)"
    )

    return [sys.executable, "-c", runner, str(summary_path)]


def _stage_c4_command(log_dir: Path) -> Sequence[str]:
    """Return the Stage C4 drill command writing artifacts into ``log_dir``."""

    script_path = _SCRIPTS_DIR / "stage_c_mcp_drill.py"
    return [
        sys.executable,
        str(script_path),
        str(log_dir),
        "--json",
    ]


@router.post("/alpha/stage-c1-exit-checklist")
async def stage_c1_exit_checklist() -> dict[str, Any]:
    """Validate the Stage C exit checklist and archive the output."""

    command = [
        sys.executable,
        str(_SCRIPTS_DIR / "validate_absolute_protocol_checklist.py"),
    ]
    result = await _run_stage_workflow(
        _STAGE_C_ROOT,
        "stage_c1_exit_checklist",
        command,
        metrics_extractor=_stage_c1_metrics,
    )
    result = _attach_summary_artifacts(result)
    if result.get("status") != "success":
        failures = result.get("failures") or []
        if failures:
            return JSONResponse(status_code=400, content=result)
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Stage C1 exit checklist failed"),
        )
    return result


@router.post("/alpha/stage-c2-demo-storyline")
async def stage_c2_demo_storyline() -> dict[str, Any]:
    """Run the scripted demo harness and capture Stage C telemetry."""

    result = await _run_stage_workflow(
        _STAGE_C_ROOT,
        "stage_c2_demo_storyline",
        _stage_c2_command,
        metrics_extractor=_stage_c2_metrics,
    )
    result = _attach_summary_artifacts(result)
    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Stage C2 demo storyline failed"),
        )
    return result


@router.post("/alpha/stage-c3-readiness-sync")
async def stage_c3_readiness_sync() -> dict[str, Any]:
    """Merge Stage A/B readiness evidence for the Stage C review."""

    result = await _run_stage_workflow(
        _STAGE_C_ROOT,
        _STAGE_C3_SLUG,
        _stage_c3_command,
        metrics_extractor=_stage_c3_metrics,
    )
    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Stage C3 readiness sync failed"),
        )
    return result


@router.post("/alpha/stage-c4-operator-mcp-drill")
async def stage_c4_operator_mcp_drill() -> dict[str, Any]:
    """Exercise the MCP adapter handshake and heartbeat for Stage C."""

    result = await _run_stage_workflow(
        _STAGE_C_ROOT,
        "stage_c4_operator_mcp_drill",
        _stage_c4_command,
        metrics_extractor=_stage_c4_metrics,
    )
    if result.get("status") == "success":
        try:
            _attach_rest_grpc_parity(result)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Stage C4 operator MCP drill failed"),
        )
    return result


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
    log_path = _REPO_ROOT / "logs" / "razar_mission.log"
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
    path = _REPO_ROOT / "logs" / "agent_interactions.jsonl"
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


if _HAS_MULTIPART:

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
                raise HTTPException(
                    status_code=500, detail="failed to store file"
                ) from exc

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
