from __future__ import annotations

"""Convenience imports for the INANNA AI agent."""

import builtins as _builtins

from . import benchmark_preprocess
from . import inanna_ai as _inanna_ai
from . import model, preprocess, source_loader

# Re-export the CLI entry point for convenience
INANNA_AI = _inanna_ai.main

# Expose the module itself so tests can monkeypatch its internals without
# performing an explicit import.  This mirrors behaviour of the original test
# suite which assumes a global ``inanna_ai`` name is available.
_builtins.inanna_ai = _inanna_ai

__all__ = [
    "INANNA_AI",
    "inanna_ai",
    "preprocess",
    "source_loader",
    "benchmark_preprocess",
    "model",
]

# Keep a module-level reference for explicit imports if needed
inanna_ai = _inanna_ai
