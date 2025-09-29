"""MCP adapter shim for operator connectors."""

from __future__ import annotations

__version__ = "0.1.0"

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from .base import ConnectorHeartbeat
from .crown_handshake_stage_b import doctrine_compliant as crown_doctrine
from .operator_api_stage_b import (
    doctrine_compliant as operator_api_doctrine,
    handshake as operator_api_handshake,
    send_heartbeat as operator_api_send_heartbeat,
)
from .operator_upload_stage_b import doctrine_compliant as operator_upload_doctrine

LOGGER = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]

STAGE_B_TARGET_SERVICES: tuple[str, ...] = (
    "operator_api",
    "operator_upload",
    "crown_handshake",
)
ROTATION_WINDOW_HOURS = 48
_ROTATION_LOG = _REPO_ROOT / "logs" / "stage_b_rotation_drills.jsonl"
_STAGE_C_ROOT = _REPO_ROOT / "logs" / "stage_c"
_STAGE_C_DRILL_STAGE = "stage_c4_operator_mcp_drill"

StageCHandshakeResult = tuple[Mapping[str, Any] | None, dict[str, str | None]]
_CONNECTOR_INDEX = _REPO_ROOT / "docs" / "connectors" / "CONNECTOR_INDEX.md"
_AUDIT_DOC = _REPO_ROOT / "docs" / "connectors" / "operator_mcp_audit.md"


def _isoformat(value: datetime) -> str:
    """Return ``value`` formatted as a UTC ISO-8601 string with ``Z`` suffix."""

    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


class OperatorMCPAdapter(ConnectorHeartbeat):
    """Adapter providing MCP handshake and heartbeat wrappers for operators."""

    def __init__(
        self,
        *,
        channel: str = "operator",
        heartbeat_interval: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(channel, interval=heartbeat_interval)
        self._client = client
        self._session: Mapping[str, Any] | None = None

    async def ensure_handshake(self) -> dict[str, Any]:
        """Perform the Stage B handshake and store the resulting session."""

        handshake_data = await operator_api_handshake(self._client)
        session_info = handshake_data.get("session")
        if isinstance(session_info, Mapping):
            self._session = session_info
        else:
            self._session = None
        LOGGER.debug("operator MCP handshake stored session=%s", self._session)
        return handshake_data

    async def emit_stage_b_heartbeat(
        self,
        payload: Mapping[str, Any] | None = None,
        *,
        credential_expiry: datetime | str | None = None,
    ) -> dict[str, Any]:
        """Emit a heartbeat with canonical Stage B metadata."""

        if self._session is None:
            handshake_data = await self.ensure_handshake()
            session_candidate = handshake_data.get("session")
            if isinstance(session_candidate, Mapping):
                self._session = session_candidate

        heartbeat_payload = dict(payload or {})
        await operator_api_send_heartbeat(
            heartbeat_payload,
            session=self._session,
            credential_expiry=credential_expiry,
            client=self._client,
        )
        return heartbeat_payload

    def doctrine_report(self) -> tuple[bool, list[str]]:
        """Return doctrine compliance status for the operator MCP adoption."""

        return evaluate_operator_doctrine()


def _parse_rotation_timestamp(value: Any) -> datetime | None:
    """Return ``value`` parsed as an aware UTC datetime when possible."""

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _extract_rotation_metadata(
    handshake: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Return rotation metadata contained within ``handshake``."""

    if not isinstance(handshake, Mapping):
        return {}
    rotation_section: Any = handshake.get("rotation")
    echo = handshake.get("echo")
    if isinstance(echo, Mapping) and not rotation_section:
        rotation_section = echo.get("rotation")
    return rotation_section if isinstance(rotation_section, Mapping) else {}


def _format_duration_iso(delta: timedelta) -> str:
    """Return ``delta`` encoded as an ISO-8601 duration string."""

    total_seconds = int(delta.total_seconds())
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = (total_seconds // 3600) % 24
    days = total_seconds // 86400

    parts: list[str] = ["P"]
    if days:
        parts.append(f"{days}D")
    time_parts: list[str] = []
    if hours:
        time_parts.append(f"{hours}H")
    if minutes:
        time_parts.append(f"{minutes}M")
    if seconds or not (days or hours or minutes):
        time_parts.append(f"{seconds}S")
    if time_parts:
        parts.append("T")
        parts.extend(time_parts)
    return "".join(parts)


def _extract_credential_window(
    handshake: Mapping[str, Any] | None,
    *,
    fallback_start: datetime | None = None,
) -> Mapping[str, Any]:
    """Return credential validity window details for ``handshake``."""

    if not isinstance(handshake, Mapping):
        return {}

    session = handshake.get("session")
    issued_at_raw: Any = None
    if isinstance(session, Mapping):
        issued_at_raw = session.get("issued_at")
    rotation = _extract_rotation_metadata(handshake)
    if issued_at_raw is None and isinstance(rotation, Mapping):
        issued_at_raw = rotation.get("last_rotated")

    issued_at = _parse_rotation_timestamp(issued_at_raw) or fallback_start

    expiry_raw: Any = None
    if isinstance(session, Mapping):
        expiry_raw = session.get("credential_expiry")
    expiry_at = _parse_rotation_timestamp(expiry_raw)

    window: dict[str, Any] = {}
    if issued_at is not None:
        window["issued_at"] = _isoformat(issued_at)
    if expiry_raw:
        window["expires_at"] = expiry_raw
    if issued_at is not None and expiry_at is not None and expiry_at >= issued_at:
        window["duration"] = _format_duration_iso(expiry_at - issued_at)
    if rotation:
        window.setdefault("rotation_window_id", rotation.get("window_id"))
    return window


def _resolve_rotation_window(
    *,
    rotated_at: datetime,
    window_hours: int,
    duration_hint: str | None,
) -> dict[str, str]:
    """Return structured rotation window metadata for the ledger."""

    duration = duration_hint or f"PT{window_hours}H"
    expires_at = rotated_at + timedelta(hours=window_hours)
    window_id = f"{rotated_at.strftime('%Y%m%dT%H%M%SZ')}-{duration}"
    return {
        "window_id": window_id,
        "started_at": _isoformat(rotated_at),
        "expires_at": _isoformat(expires_at),
        "duration": duration,
    }


def _resolve_repo_path(value: Any) -> Path | None:
    """Return ``value`` as an absolute path when possible."""

    if not value:
        return None
    try:
        candidate = Path(str(value))
    except TypeError:
        return None
    if not candidate.is_absolute():
        candidate = (_REPO_ROOT / candidate).resolve()
    return candidate


def _load_json(path: Path | None) -> Mapping[str, Any] | None:
    """Safely load JSON from ``path`` when the file exists."""

    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _extract_latency(trace: Mapping[str, Any] | None) -> float | None:
    """Return a latency value in milliseconds when present in ``trace``."""

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


def collect_transport_parity_artifacts(
    stage_c_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Return Stage C transport parity artifacts summarised for monitoring."""

    root = Path(stage_c_root) if stage_c_root is not None else _STAGE_C_ROOT
    entries: list[dict[str, Any]] = []
    if not root.exists():
        return entries

    for summary_path in sorted(root.glob("*/summary.json")):
        summary_data = _load_json(summary_path)
        if not isinstance(summary_data, Mapping):
            continue

        summary_section = summary_data.get("summary")
        if not isinstance(summary_section, Mapping):
            continue

        artifacts = summary_section.get("handshake_artifacts")
        if not isinstance(artifacts, Mapping):
            continue

        rest_path = _resolve_repo_path(artifacts.get("rest"))
        grpc_path = _resolve_repo_path(artifacts.get("grpc"))
        diff_path = _resolve_repo_path(artifacts.get("diff"))

        rest_payload = _load_json(rest_path)
        grpc_payload = _load_json(grpc_path)
        diff_payload = _load_json(diff_path)

        rest_handshake: Mapping[str, Any] | None = None
        if isinstance(rest_payload, Mapping):
            candidate = rest_payload.get("normalized")
            if isinstance(candidate, Mapping):
                rest_handshake = candidate
            else:
                candidate = rest_payload.get("handshake")
                rest_handshake = candidate if isinstance(candidate, Mapping) else None

        grpc_handshake: Mapping[str, Any] | None = None
        grpc_metadata: Mapping[str, Any] | None = None
        if isinstance(grpc_payload, Mapping):
            candidate = grpc_payload.get("handshake_equivalent")
            if not isinstance(candidate, Mapping):
                trace_section = grpc_payload.get("trace")
                if isinstance(trace_section, Mapping):
                    response = trace_section.get("response")
                    if isinstance(response, Mapping):
                        candidate = response.get("handshake_equivalent")
            if isinstance(candidate, Mapping):
                grpc_handshake = candidate
            metadata_section = grpc_payload.get("metadata")
            if isinstance(metadata_section, Mapping):
                grpc_metadata = metadata_section

        rest_normalized = normalize_handshake_for_trace(rest_handshake)
        grpc_normalized = normalize_handshake_for_trace(grpc_handshake)

        rest_checksum = None
        if isinstance(rest_payload, Mapping):
            checksum_value = rest_payload.get("checksum")
            if isinstance(checksum_value, str):
                rest_checksum = checksum_value
        if rest_checksum is None:
            rest_checksum = compute_handshake_checksum(rest_handshake)

        grpc_checksum = None
        if isinstance(grpc_payload, Mapping):
            checksum_value = grpc_payload.get("checksum")
            if isinstance(checksum_value, str):
                grpc_checksum = checksum_value
            elif isinstance(grpc_metadata, Mapping):
                parity_checksum = grpc_metadata.get("parity_checksum")
                if isinstance(parity_checksum, str):
                    grpc_checksum = parity_checksum
        if grpc_checksum is None:
            grpc_checksum = compute_handshake_checksum(grpc_handshake)

        parity_flag = None
        checksum_match: bool | None = None
        differences: list[Any] = []
        rotation_window: Mapping[str, Any] | None = None
        if isinstance(diff_payload, Mapping):
            parity_candidate = diff_payload.get("parity")
            if isinstance(parity_candidate, bool):
                parity_flag = parity_candidate
            checksum_candidate = diff_payload.get("checksum_match")
            if isinstance(checksum_candidate, bool):
                checksum_match = checksum_candidate
            raw_differences = diff_payload.get("differences")
            if isinstance(raw_differences, Sequence) and not isinstance(
                raw_differences, (str, bytes)
            ):
                differences = list(raw_differences)
            rotation_candidate = diff_payload.get("rotation_window")
            if isinstance(rotation_candidate, Mapping):
                rotation_window = rotation_candidate

        if parity_flag is None:
            parity_value = summary_section.get("rest_grpc_parity")
            if isinstance(parity_value, bool):
                parity_flag = parity_value

        if checksum_match is None and rest_checksum and grpc_checksum:
            checksum_match = rest_checksum == grpc_checksum

        trial_trace = summary_section.get("trial_trace")
        rest_trace: Mapping[str, Any] | None = None
        grpc_trace: Mapping[str, Any] | None = None
        if isinstance(trial_trace, Mapping):
            rest_trace_candidate = trial_trace.get("rest")
            if isinstance(rest_trace_candidate, Mapping):
                rest_trace = rest_trace_candidate
            grpc_trace_candidate = trial_trace.get("grpc")
            if isinstance(grpc_trace_candidate, Mapping):
                grpc_trace = grpc_trace_candidate

        rest_latency = _extract_latency(rest_trace)
        grpc_latency = _extract_latency(grpc_trace)

        monitoring_gaps: list[str] = []
        if rest_latency is None:
            monitoring_gaps.append("rest_latency_missing")
        if grpc_latency is None:
            monitoring_gaps.append("grpc_latency_missing")

        heartbeat_emitted_raw = summary_section.get("heartbeat_emitted")
        heartbeat_emitted = bool(heartbeat_emitted_raw)
        if not heartbeat_emitted:
            monitoring_gaps.append("heartbeat_missing")

        entry = {
            "run_id": summary_path.parent.name,
            "summary_path": str(summary_path),
            "rest_path": str(rest_path) if rest_path else None,
            "grpc_path": str(grpc_path) if grpc_path else None,
            "diff_path": str(diff_path) if diff_path else None,
            "rest_checksum": rest_checksum,
            "grpc_checksum": grpc_checksum,
            "checksum_match": checksum_match,
            "parity": parity_flag if parity_flag is not None else bool(checksum_match),
            "differences": differences,
            "normalized": {
                "rest": rest_normalized,
                "grpc": grpc_normalized,
            },
            "latency_ms": {
                "rest": rest_latency,
                "grpc": grpc_latency,
            },
            "monitoring_gaps": monitoring_gaps,
            "heartbeat_emitted": heartbeat_emitted,
            "metadata": {
                "rest": {
                    "credential_expiry": (
                        rest_payload.get("credential_expiry")
                        if isinstance(rest_payload, Mapping)
                        else None
                    ),
                },
                "grpc": {
                    "recorded_at": (
                        grpc_metadata.get("recorded_at")
                        if isinstance(grpc_metadata, Mapping)
                        else None
                    ),
                    "credential_expiry": (
                        grpc_metadata.get("credential_expiry")
                        if isinstance(grpc_metadata, Mapping)
                        else None
                    ),
                },
                "rotation_window": rotation_window,
            },
        }

        entries.append(entry)

    return entries


def build_transport_parity_monitoring_payload(
    stage_c_root: Path | None = None,
) -> dict[str, Any]:
    """Return monitoring metadata for the latest Stage C transport parity run."""

    entries = collect_transport_parity_artifacts(stage_c_root=stage_c_root)
    if not entries:
        return {
            "parity": False,
            "alerts": ["no_stage_c_transport_artifacts"],
        }

    latest = entries[-1]
    alerts = list(latest.get("monitoring_gaps") or [])
    if latest.get("differences"):
        alerts.append("handshake_differences_detected")
    if latest.get("checksum_match") is False:
        alerts.append("checksum_mismatch")

    payload = {
        "parity": bool(latest.get("parity")),
        "checksum_match": latest.get("checksum_match"),
        "rest_checksum": latest.get("rest_checksum"),
        "grpc_checksum": latest.get("grpc_checksum"),
        "latency_ms": latest.get("latency_ms"),
        "alerts": alerts,
        "run_id": latest.get("run_id"),
        "summary_path": latest.get("summary_path"),
        "heartbeat_emitted": latest.get("heartbeat_emitted"),
    }

    return payload


def load_latest_stage_c_handshake() -> StageCHandshakeResult:
    """Return the latest successful Stage C MCP drill handshake and metadata."""

    handshake: Mapping[str, Any] | None = None
    metadata: dict[str, str | None] = {
        "summary_path": None,
        "handshake_path": None,
        "completed_at": None,
    }
    if not _STAGE_C_ROOT.exists():
        return handshake, metadata

    best_sort_key: tuple[int, datetime, str] | None = None
    for summary_path in sorted(_STAGE_C_ROOT.glob("*/summary.json")):
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if summary.get("stage") != _STAGE_C_DRILL_STAGE:
            continue
        if summary.get("status") != "success":
            continue

        completed_at_raw = summary.get("completed_at")
        completed_at = _parse_rotation_timestamp(completed_at_raw)
        artifacts = summary.get("artifacts")
        handshake_candidate: Mapping[str, Any] | None = None
        handshake_path: Path | None = None
        if isinstance(artifacts, Mapping):
            handshake_value = artifacts.get("mcp_handshake")
            handshake_path = _resolve_repo_path(handshake_value)
            if handshake_path and handshake_path.exists():
                try:
                    handshake_candidate = json.loads(
                        handshake_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError):
                    handshake_candidate = None

        if handshake_candidate is None:
            metrics = summary.get("metrics")
            if isinstance(metrics, Mapping):
                metrics_handshake = metrics.get("handshake")
                if isinstance(metrics_handshake, Mapping):
                    handshake_candidate = metrics_handshake

        if handshake_candidate is None:
            continue

        iso_completed: str | None = None
        if completed_at:
            iso_completed = _isoformat(completed_at)
        elif isinstance(completed_at_raw, str):
            try:
                fallback_dt = datetime.fromisoformat(
                    completed_at_raw.replace("Z", "+00:00")
                )
            except ValueError:
                fallback_dt = None
            if fallback_dt is not None:
                if fallback_dt.tzinfo is None:
                    fallback_dt = fallback_dt.replace(tzinfo=timezone.utc)
                iso_completed = _isoformat(fallback_dt)

        candidate_key = (
            1 if completed_at else 0,
            completed_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
            summary_path.name,
        )
        if best_sort_key is None or candidate_key > best_sort_key:
            handshake = handshake_candidate
            metadata = {
                "summary_path": str(summary_path),
                "handshake_path": str(handshake_path) if handshake_path else None,
                "completed_at": iso_completed,
            }
            best_sort_key = candidate_key

    return handshake, metadata


def record_rotation_drill(
    connector_id: str,
    *,
    rotated_at: datetime | str | None = None,
    window_hours: int = ROTATION_WINDOW_HOURS,
    handshake: Mapping[str, Any] | None = None,
    context_status: Mapping[str, Mapping[str, Any]] | None = None,
    traces: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a credential rotation drill entry for ``connector_id``.

    ``context_status`` can embed downstream promotion metadata (for example,
    Stage C adoption evidence) that should travel with the ledger entry.
    """

    rotation_metadata = _extract_rotation_metadata(handshake)
    rotation_timestamp = _parse_rotation_timestamp(
        rotated_at if rotated_at is not None else rotation_metadata.get("last_rotated")
    )
    timestamp = rotation_timestamp or datetime.now(timezone.utc)

    duration_hint: str | None = None
    rotation_window_raw = rotation_metadata.get("rotation_window")
    if isinstance(rotation_window_raw, str):
        duration_hint = rotation_window_raw

    credential_window = _extract_credential_window(
        handshake, fallback_start=rotation_timestamp
    )

    entry = {
        "connector_id": connector_id,
        "rotated_at": _isoformat(timestamp),
        "window_hours": window_hours,
        "rotation_window": _resolve_rotation_window(
            rotated_at=timestamp,
            window_hours=window_hours,
            duration_hint=duration_hint,
        ),
    }
    if credential_window:
        entry["credential_window"] = dict(credential_window)
    if context_status:
        entry["context_status"] = {
            key: dict(value)
            for key, value in context_status.items()
            if isinstance(key, str) and isinstance(value, Mapping)
        }

    if traces:
        entry["traces"] = _coerce_trace_payload(traces)

    _ROTATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _ROTATION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    LOGGER.info("Recorded Stage B rotation drill", extra=entry)
    return entry


def load_rotation_history() -> list[dict[str, Any]]:
    """Return recorded rotation drills."""

    if not _ROTATION_LOG.exists():
        return []
    return [
        json.loads(line)
        for line in _ROTATION_LOG.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evaluate_operator_doctrine() -> tuple[bool, list[str]]:
    """Validate doctrine requirements tied to the operator MCP migration."""

    failures: list[str] = []

    audit_exists = _AUDIT_DOC.exists()
    if not audit_exists:
        failures.append(f"audit document missing: {_AUDIT_DOC}")

    try:
        connector_index = _CONNECTOR_INDEX.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"connector index missing: {_CONNECTOR_INDEX}")
        connector_index = ""

    if "operator_mcp_audit.md" not in connector_index:
        failures.append("connector index not referencing MCP audit")
    if "MCP adapter stub" not in connector_index:
        failures.append("connector index missing MCP adapter status note")

    rotation_entries = load_rotation_history()
    if not rotation_entries:
        failures.append("no credential rotation drills recorded")
    else:
        latest = rotation_entries[-1]
        if latest.get("window_hours") != ROTATION_WINDOW_HOURS:
            failures.append("latest rotation drill does not confirm 48-hour window")
        rotation_window = latest.get("rotation_window")
        if not isinstance(rotation_window, Mapping):
            failures.append("latest rotation drill missing rotation_window metadata")
        else:
            for field in ("window_id", "started_at", "expires_at", "duration"):
                if field not in rotation_window:
                    failures.append(f"rotation_window missing field: {field}")

    for name, doctrine_check in (
        ("operator_api_stage_b", operator_api_doctrine),
        ("operator_upload_stage_b", operator_upload_doctrine),
        ("crown_handshake_stage_b", crown_doctrine),
    ):
        ok, issues = doctrine_check()
        if not ok:
            failures.extend(f"{name}: {issue}" for issue in issues)

    return (not failures, failures)


def stage_b_context_enabled() -> bool:
    """Return True when MCP toggles indicate Stage B rehearsals are active."""

    return os.getenv("ABZU_USE_MCP") == "1"


def _coerce_trace_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``value`` coerced to a JSON-serialisable mapping."""

    def _convert(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): _convert(val)
                for key, val in item.items()
                if isinstance(key, str)
            }
        if isinstance(item, (list, tuple, set)):
            return [_convert(element) for element in item]
        return item

    return _convert(value)


def normalize_handshake_for_trace(
    handshake: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return ``handshake`` normalised for REST↔gRPC parity checks."""

    if not isinstance(handshake, Mapping):
        return {}

    normalized: dict[str, Any] = {}

    authenticated = handshake.get("authenticated")
    if isinstance(authenticated, bool):
        normalized["authenticated"] = authenticated

    session = handshake.get("session")
    if isinstance(session, Mapping):
        session_view: dict[str, Any] = {}
        for key in ("id", "credential_expiry", "issued_at"):
            value = session.get(key)
            if value is not None:
                session_view[key] = value
        if session_view:
            normalized["session"] = session_view

    contexts = handshake.get("accepted_contexts")
    context_entries: list[dict[str, Any]] = []
    if isinstance(contexts, Sequence):
        for raw in contexts:
            if isinstance(raw, Mapping):
                entry: dict[str, Any] = {}
                for key in (
                    "name",
                    "status",
                    "promoted_at",
                    "evidence_path",
                    "summary_path",
                ):
                    value = raw.get(key)
                    if value is not None:
                        entry[key] = value
                if entry:
                    context_entries.append(entry)
            elif isinstance(raw, str):
                context_entries.append({"name": raw, "status": "accepted"})
    if context_entries:
        context_entries.sort(key=lambda item: item.get("name", ""))
        normalized["accepted_contexts"] = context_entries

    rotation = _extract_rotation_metadata(handshake)
    if rotation:
        rotation_view: dict[str, Any] = {}
        for key in ("connector_id", "last_rotated", "rotation_window", "window_id"):
            value = rotation.get(key)
            if value is not None:
                rotation_view[key] = value
        if rotation_view:
            normalized["rotation"] = rotation_view

    echo = handshake.get("echo")
    if isinstance(echo, Mapping):
        echo_view: dict[str, Any] = {}
        rotation_echo = echo.get("rotation")
        if isinstance(rotation_echo, Mapping):
            echo_rotation: dict[str, Any] = {}
            for key in ("connector_id", "last_rotated", "rotation_window", "window_id"):
                value = rotation_echo.get(key)
                if value is not None:
                    echo_rotation[key] = value
            if echo_rotation:
                echo_view["rotation"] = echo_rotation
        if echo_view:
            normalized["echo"] = echo_view

    return normalized


def compute_handshake_checksum(handshake: Mapping[str, Any] | None) -> str | None:
    """Return a SHA-256 checksum for ``handshake`` after normalisation."""

    normalized = normalize_handshake_for_trace(handshake)
    if not normalized:
        return None
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def latest_rotation_entry(connector_id: str) -> Mapping[str, Any] | None:
    """Return the most recent rotation ledger entry for ``connector_id``."""

    history = load_rotation_history()
    for entry in reversed(history):
        if entry.get("connector_id") == connector_id:
            return entry
    return None


__all__ = [
    "OperatorMCPAdapter",
    "STAGE_B_TARGET_SERVICES",
    "ROTATION_WINDOW_HOURS",
    "record_rotation_drill",
    "load_rotation_history",
    "load_latest_stage_c_handshake",
    "collect_transport_parity_artifacts",
    "build_transport_parity_monitoring_payload",
    "evaluate_operator_doctrine",
    "stage_b_context_enabled",
    "normalize_handshake_for_trace",
    "compute_handshake_checksum",
    "latest_rotation_entry",
]
