#!/usr/bin/env python3
"""Wrapper to validate component_index.json."""
from __future__ import annotations

from validate_component_index_json import main as validate

__version__ = "0.1.0"

if __name__ == "__main__":
    raise SystemExit(validate())
