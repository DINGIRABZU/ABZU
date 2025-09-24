#!/usr/bin/env python3
"""Stage C MCP drill capturing handshake and heartbeat artifacts."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
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
    record_rotation_drill("operator_api", rotated_at=credential_expiry)

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
