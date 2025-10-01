"""Recorded REST↔gRPC parity contract suites for APSU transports."""

from __future__ import annotations

from pathlib import Path
from typing import Final

FIXTURE_ROOT: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "transport_parity"

STAGE_E_CONNECTORS: Final[tuple[str, ...]] = (
    "operator_api",
    "operator_upload",
    "crown_handshake",
)

__all__ = ["FIXTURE_ROOT", "STAGE_E_CONNECTORS"]
