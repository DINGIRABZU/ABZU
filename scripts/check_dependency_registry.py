#!/usr/bin/env python3
"""Wrapper to validate docs/dependency_registry.md."""
from __future__ import annotations

from verify_dependencies import main as verify

__version__ = "0.1.0"

if __name__ == "__main__":
    raise SystemExit(verify())
