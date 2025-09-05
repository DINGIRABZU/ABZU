#!/usr/bin/env python3
"""Initialize all memory layers and report readiness."""
from __future__ import annotations

import logging

from memory.bundle import MemoryBundle

__version__ = "0.1.0"


def main() -> None:
    """Bootstrap memory layers and log their status."""
    logging.basicConfig(level=logging.INFO)
    bundle = MemoryBundle()
    statuses = bundle.initialize()
    for layer, status in statuses.items():
        logging.info("%s: %s", layer, status)


if __name__ == "__main__":
    main()
