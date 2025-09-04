"""List of core modules required for Spiral OS boot diagnostics."""

from __future__ import annotations

VITAL_MODULES = [
    "requests",
    "server",
    "invocation_engine",
    "emotional_state",
    "logging",
]

__all__ = ["VITAL_MODULES"]
