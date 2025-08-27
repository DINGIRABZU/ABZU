from __future__ import annotations

"""Re-export quarantine utilities for RAZAR agents.

This thin wrapper exposes :mod:`razar.quarantine_manager` functionality within
the ``agents.razar`` namespace so remote code agents can submit diagnostics and
trigger component reactivation.
"""

from razar.quarantine_manager import (
    is_quarantined,
    quarantine_component,
    record_diagnostics,
    reactivate_component,
    resolve_component,
)

__all__ = [
    "is_quarantined",
    "quarantine_component",
    "record_diagnostics",
    "reactivate_component",
    "resolve_component",
]

