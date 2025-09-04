#!/usr/bin/env python3
"""Compact or purge memory layers."""

from __future__ import annotations

import gc


def main() -> None:
    gc.collect()


if __name__ == "__main__":
    main()
