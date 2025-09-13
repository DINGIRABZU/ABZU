"""Compatibility wrapper for :mod:`core.feedback_logging`.

Provides legacy import support while exposing key constants and functions
from :mod:`core.feedback_logging` at the top level.  Older modules import
``feedback_logging`` directly; this shim forwards those imports to the
modern location so attributes such as ``NOVELTY_THRESHOLD`` remain
available for backwards compatibility.
"""

from __future__ import annotations

from core.feedback_logging import (
    COHERENCE_THRESHOLD,
    LOG_FILE,
    NOVELTY_THRESHOLD,
    append_feedback,
    load_feedback,
)

__all__ = [
    "append_feedback",
    "load_feedback",
    "LOG_FILE",
    "NOVELTY_THRESHOLD",
    "COHERENCE_THRESHOLD",
]
