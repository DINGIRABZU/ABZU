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
import re
import shutil
import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Mapping, Sequence

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
    ROTATION_WINDOW_HOURS,
    OperatorMCPAdapter,
    load_rotation_history,
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

_REPO_ROOT = Path(__file__).resolve().parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"

_STAGE_A_ROOT = _REPO_ROOT / "logs" / "stage_a"
_STAGE_B_ROOT = _REPO_ROOT / "logs" / "stage_b"
_STAGE_C_ROOT = _REPO_ROOT / "logs" / "stage_c"
_STAGE_C_BUNDLE_FILENAME = "readiness_bundle.json"


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
    for line in reversed(stdout_lines):
        stripped = line.strip()
        if not stripped:
            continue
        if not summary_line:
            summary_line = stripped
        if summary_json is None and stripped.startswith("{"):
            try:
                candidate = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, Mapping):
                summary_json = candidate
                break

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
    if isinstance(connectors, Mapping):
        for connector_id, record in connectors.items():
            if not isinstance(record, Mapping):
                continue
            handshake = record.get("handshake_response")
            if isinstance(handshake, Mapping):
                accepted = handshake.get("accepted_contexts")
            else:
                accepted = None
            connectors_summary[str(connector_id)] = {
                "module": record.get("module"),
                "doctrine_ok": record.get("doctrine_ok"),
                "supported_channels": record.get("supported_channels"),
                "capabilities": record.get("capabilities"),
                "accepted_contexts": accepted,
            }

    return {
        "generated_at": data.get("generated_at"),
        "stage": data.get("stage"),
        "context": data.get("context"),
        "connectors": connectors_summary,
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

    latest_indices: dict[str, int] = {}
    for index, entry in enumerate(rotation_history):
        connector_id = entry.get("connector_id")
        if isinstance(connector_id, str):
            latest_indices[connector_id] = index

    connector_entries: list[Mapping[str, Any]] = []
    for connector_id in connectors:
        index = latest_indices.get(connector_id)
        if index is not None:
            connector_entries.append(rotation_history[index])
    if not connector_entries and rotation_history:
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
    lines = [line.strip() for line in stdout_text.splitlines() if line.strip()]
    unchecked = [line for line in lines if line.startswith("- [ ]")]
    status_failure_pattern = re.compile(r"status:\s*(failed|blocked)\b", re.IGNORECASE)
    failing = [
        line
        for line in lines
        if line.startswith("- [") and status_failure_pattern.search(line)
    ]
    completed = not unchecked and not failing
    summary_line = next(
        (line for line in reversed(lines) if not line.startswith("- [ ]")), ""
    )
    metrics = {
        "completed": completed,
        "unchecked_count": len(unchecked),
        "unchecked_items": unchecked,
        "failing_count": len(failing),
        "failing_items": failing,
        "message": summary_line or None,
    }
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
    bundle_data: dict[str, Any] | None = None
    metrics: dict[str, Any] = {
        "bundle_path": str(bundle_path) if bundle_path.exists() else None,
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
            summary_text = stage_b_summary.get("summary")
            if isinstance(summary_text, str) and summary_text.strip():
                rotation_info["summary"] = summary_text
            metrics_block = stage_b_summary.get("metrics")
            if isinstance(metrics_block, Mapping):
                rotation_window = metrics_block.get("rotation_window")
                if isinstance(rotation_window, Mapping):
                    rotation_info["window"] = dict(rotation_window)
                credential_expiry_value = metrics_block.get(
                    "heartbeat_expiry"
                ) or metrics_block.get("credential_expiry")
                if credential_expiry_value:
                    rotation_info["credential_expiry"] = credential_expiry_value
        if rotation_info:
            merged_payload["rotation"] = rotation_info

        if stage_a_status == "success" and stage_b_status == "success":
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

    if bundle_data:
        bundle_data.setdefault("stage_a", stage_a_section)
        bundle_data.setdefault("stage_b", stage_b_section)
        bundle_data["merged"] = merged_snapshot
        metrics["bundle"] = bundle_data

    artifacts = payload.setdefault("artifacts", {})
    if bundle_path.exists():
        artifacts.setdefault("readiness_bundle", str(bundle_path))

    stage_a_slug_sections = stage_a_section.get("slugs")
    if isinstance(stage_a_slug_sections, Mapping) and stage_a_slug_sections:
        for slug, slug_section in stage_a_slug_sections.items():
            if not isinstance(slug_section, Mapping):
                continue
            slug_key = str(slug).lower()
            summary_path = slug_section.get("summary_path")
            if summary_path:
                artifacts.setdefault(f"stage_a_{slug_key}_summary", str(summary_path))
            artifacts_list = slug_section.get("artifacts") or []
            for index, artifact_path in enumerate(artifacts_list):
                artifacts.setdefault(
                    f"stage_a_{slug_key}_artifact_{index + 1}",
                    str(artifact_path),
                )
    else:
        summary_path = stage_a_section.get("summary_path")
        if summary_path:
            artifacts.setdefault("stage_a_summary", str(summary_path))
        for index, artifact_path in enumerate(stage_a_section.get("artifacts") or []):
            artifacts.setdefault(f"stage_a_artifact_{index + 1}", str(artifact_path))

    summary_path_b = stage_b_section.get("summary_path")
    if summary_path_b:
        artifacts.setdefault("stage_b_summary", str(summary_path_b))
    for index, artifact_path in enumerate(stage_b_section.get("artifacts") or []):
        artifacts.setdefault(f"stage_b_artifact_{index + 1}", str(artifact_path))

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

    heartbeat_emitted = bool(heartbeat_payload)

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
    if handshake_error:
        metrics["handshake_error"] = handshake_error
    if heartbeat_error:
        metrics["heartbeat_error"] = heartbeat_error

    if handshake_error or heartbeat_error:
        payload["status"] = "error"
        payload["error"] = "; ".join(
            message for message in (handshake_error, heartbeat_error) if message
        )

    return metrics


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

    command = [sys.executable, str(_SCRIPTS_DIR / "bootstrap.py")]
    return await _run_stage_workflow(_STAGE_A_ROOT, "stage_a1_boot_telemetry", command)


@router.post("/alpha/stage-a2-crown-replays")
async def stage_a2_crown_replays() -> dict[str, Any]:
    """Capture Crown replay evidence for Stage A auditing."""

    command = [sys.executable, str(_SCRIPTS_DIR / "crown_capture_replays.py")]
    return await _run_stage_workflow(_STAGE_A_ROOT, "stage_a2_crown_replays", command)


@router.post("/alpha/stage-a3-gate-shakeout")
async def stage_a3_gate_shakeout() -> dict[str, Any]:
    """Run the Alpha gate automation shakeout script."""

    command = ["bash", str(_SCRIPTS_DIR / "run_alpha_gate.sh")]
    return await _run_stage_workflow(_STAGE_A_ROOT, "stage_a3_gate_shakeout", command)


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
    return [
        sys.executable,
        str(_SCRIPTS_DIR / "aggregate_stage_readiness.py"),
        str(log_dir),
    ]


def _stage_c4_command(log_dir: Path) -> Sequence[str]:
    return [
        sys.executable,
        str(_SCRIPTS_DIR / "stage_c_mcp_drill.py"),
        "--json",
        str(log_dir),
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
    if result.get("status") != "success":
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
        "stage_c3_readiness_sync",
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
