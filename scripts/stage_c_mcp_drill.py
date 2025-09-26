#!/usr/bin/env python3
"""Stage C MCP drill capturing handshake and heartbeat artifacts."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts._stage_runtime import bootstrap

bootstrap()

from connectors.operator_mcp_adapter import (
    ROTATION_WINDOW_HOURS,
    OperatorMCPAdapter,
    record_rotation_drill,
)

LOGGER = logging.getLogger(__name__)

_EVENT_NAME = "stage-c4-operator-mcp-drill"
_STUB_ENV_FLAG = "ABZU_STAGE_C_MCP_DRILL_STUB"


def _use_stub_adapter() -> bool:
    flag = os.getenv(_STUB_ENV_FLAG, "")
    return flag.lower() in {"1", "true", "yes", "on"}


def _build_stub_handshake(now: datetime) -> dict[str, Any]:
    rotation_window = f"PT{ROTATION_WINDOW_HOURS}H"
    rotated_at = _isoformat(now)
    rotation_metadata = {
        "connector_id": "operator_api",
        "last_rotated": rotated_at,
        "rotation_window": rotation_window,
        "window_id": f"{now.strftime('%Y%m%dT%H%M%SZ')}-{rotation_window}",
    }
    expiry = _isoformat(now + timedelta(hours=ROTATION_WINDOW_HOURS))
    return {
        "authenticated": True,
        "session": {
            "id": "stage-c-session",
            "credential_expiry": expiry,
        },
        "accepted_contexts": [
            {"name": "stage-b-rehearsal", "status": "accepted"},
            {"name": "stage-c-prep", "status": "accepted"},
        ],
        "rotation": rotation_metadata,
        "echo": {"rotation": dict(rotation_metadata)},
    }


class _StubOperatorAdapter:
    """In-memory adapter when the MCP gateway is unavailable."""

    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self._handshake = _build_stub_handshake(now)

    async def ensure_handshake(self) -> dict[str, Any]:
        LOGGER.info("Using stubbed Stage C MCP drill payload")
        LOGGER.debug("Stub handshake payload: %s", self._handshake)
        return dict(self._handshake)

    async def emit_stage_b_heartbeat(
        self,
        payload: dict[str, Any],
        *,
        credential_expiry: datetime | None = None,
    ) -> dict[str, Any]:
        heartbeat_payload = dict(payload)
        heartbeat_payload.setdefault("event", _EVENT_NAME)
        session = self._handshake.get("session", {})
        heartbeat_payload.setdefault("session", session)

        expiry_candidate: datetime | None = None
        if isinstance(credential_expiry, datetime):
            expiry_candidate = credential_expiry
        elif isinstance(session, dict):
            raw_expiry = session.get("credential_expiry")
            if isinstance(raw_expiry, str) and raw_expiry:
                try:
                    expiry_candidate = datetime.fromisoformat(
                        raw_expiry.replace("Z", "+00:00")
                    )
                except ValueError:
                    expiry_candidate = None

        if expiry_candidate is None:
            expiry_candidate = datetime.now(timezone.utc) + timedelta(
                hours=ROTATION_WINDOW_HOURS
            )

        heartbeat_payload["credential_expiry"] = _isoformat(expiry_candidate)
        return heartbeat_payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir",
        help="Directory where handshake and heartbeat artifacts will be stored.",
    )
    parser.add_argument(
        "--skip-heartbeat",
        action="store_true",
        help="Do not emit the rehearsal heartbeat during the drill.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the drill summary as JSON (default when stdout is captured).",
    )
    return parser


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


async def _run_drill(
    output_dir: Path,
    *,
    emit_heartbeat: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    adapter: OperatorMCPAdapter | _StubOperatorAdapter
    if _use_stub_adapter():
        adapter = _StubOperatorAdapter()
    else:
        adapter = OperatorMCPAdapter()
    handshake = await adapter.ensure_handshake()

    heartbeat_payload: dict[str, Any] | None = None
    credential_expiry: datetime | None = None
    if emit_heartbeat:
        credential_expiry = datetime.now(timezone.utc) + timedelta(
            hours=ROTATION_WINDOW_HOURS
        )
        heartbeat_payload = await adapter.emit_stage_b_heartbeat(
            {
                "event": _EVENT_NAME,
                "stage": "C",
            },
            credential_expiry=credential_expiry,
        )

    handshake_path = output_dir / "mcp_handshake.json"
    handshake_path.write_text(
        json.dumps(handshake, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    heartbeat_path = output_dir / "heartbeat.json"
    heartbeat_record = {
        "event": _EVENT_NAME,
        "payload": heartbeat_payload,
        "credential_expiry": _isoformat(credential_expiry),
        "rotation_window_hours": ROTATION_WINDOW_HOURS,
    }
    heartbeat_path.write_text(
        json.dumps(heartbeat_record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Record the rotation drill so doctrine checks account for this run.
    record_rotation_drill(
        "operator_api",
        rotated_at=None,
        handshake=handshake,
    )

    summary = {
        "status": "success",
        "event": _EVENT_NAME,
        "handshake_path": str(handshake_path),
        "heartbeat_path": str(heartbeat_path),
        "rotation_window_hours": ROTATION_WINDOW_HOURS,
        "credential_expiry": heartbeat_record["credential_expiry"],
        "heartbeat_emitted": heartbeat_payload is not None,
        "handshake": handshake,
        "heartbeat_payload": heartbeat_payload,
    }

    return summary


async def _async_main(args: argparse.Namespace) -> int:
    try:
        summary = await _run_drill(
            Path(args.output_dir), emit_heartbeat=not args.skip_heartbeat
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("Stage C MCP drill failed: %s", exc)
        return 1

    output = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.json:
        print(output)
    else:
        print("Stage C MCP drill completed.")
        print(output)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_async_main(args))


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
