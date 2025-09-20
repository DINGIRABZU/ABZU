#!/usr/bin/env python3
"""Stage B rehearsal smoke checks for operator connectors."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from connectors.operator_mcp_adapter import (
    ROTATION_WINDOW_HOURS,
    STAGE_B_TARGET_SERVICES,
    OperatorMCPAdapter,
    evaluate_operator_doctrine,
    record_rotation_drill,
    stage_b_context_enabled,
)

LOGGER = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-heartbeat",
        action="store_true",
        help="Do not emit the rehearsal heartbeat during the run.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results as JSON for downstream automation.",
    )
    return parser


async def _run_operator_checks(
    *,
    emit_heartbeat: bool,
) -> dict[str, Any]:
    adapter = OperatorMCPAdapter()
    handshake_data = await adapter.ensure_handshake()

    if emit_heartbeat:
        expiry = datetime.now(timezone.utc) + timedelta(hours=ROTATION_WINDOW_HOURS)
        await adapter.emit_stage_b_heartbeat(
            {"event": "stage-b-smoke"}, credential_expiry=expiry
        )

    return handshake_data


def _collect_crown_metadata() -> dict[str, Any]:
    from razar import crown_handshake

    return {
        "version": getattr(crown_handshake, "__version__", "unknown"),
        "module": getattr(crown_handshake, "__file__", "n/a"),
    }


async def run_stage_b_smoke(*, emit_heartbeat: bool = True) -> Dict[str, Any]:
    if not stage_b_context_enabled():
        raise RuntimeError("ABZU_USE_MCP=1 required for Stage B smoke checks")

    handshake = await _run_operator_checks(emit_heartbeat=emit_heartbeat)

    results: Dict[str, Any] = {
        "stage": "B",
        "targets": list(STAGE_B_TARGET_SERVICES),
        "services": {
            "operator_api": {
                "session": handshake.get("session"),
                "accepted_contexts": handshake.get("accepted_contexts"),
            },
            "operator_upload": {
                "session_reused": True,
                "notes": "Upload operations share the operator MCP session.",
            },
            "crown_handshake": _collect_crown_metadata(),
        },
    }

    for connector_id in ("operator_api", "operator_upload"):
        record_rotation_drill(connector_id)

    doctrine_ok, doctrine_failures = evaluate_operator_doctrine()
    results["doctrine_ok"] = doctrine_ok
    results["doctrine_failures"] = doctrine_failures

    return results


async def _async_main(args: argparse.Namespace) -> int:
    try:
        results = await run_stage_b_smoke(emit_heartbeat=not args.skip_heartbeat)
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("Stage B smoke checks failed: %s", exc)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("Stage B smoke checks completed.")
        print(json.dumps(results, indent=2, default=str))

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_async_main(args))


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
