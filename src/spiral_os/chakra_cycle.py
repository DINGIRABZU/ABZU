"""Chakra gear ratios and heartbeat metric emission."""

from __future__ import annotations

import time
from typing import Mapping, Iterable

from agents.event_bus import emit_event

from .pulse_emitter import CHAKRAS

__version__ = "0.1.0"

# Nominal gear ratios for each chakra in the cycle
GEAR_RATIOS: Mapping[str, float] = {
    "root": 1.0,
    "sacral": 1.2,
    "solar": 1.5,
    "heart": 1.0,
    "throat": 0.8,
    "third_eye": 1.3,
    "crown": 1.0,
}


def emit_cycle_metrics(
    chakras: Iterable[str] = CHAKRAS,
    *,
    timestamp: float | None = None,
) -> None:
    """Emit heartbeat metrics for ``chakras`` at ``timestamp``.

    Each chakra publishes its configured ``gear_ratio`` so downstream
    monitors can evaluate cadence drift.
    """

    ts = timestamp or time.time()
    for chakra in chakras:
        ratio = GEAR_RATIOS.get(chakra, 1.0)
        emit_event(
            "chakra_cycle",
            "heartbeat_metric",
            {"chakra": chakra, "gear_ratio": ratio, "timestamp": ts},
        )


__all__ = ["GEAR_RATIOS", "emit_cycle_metrics"]
