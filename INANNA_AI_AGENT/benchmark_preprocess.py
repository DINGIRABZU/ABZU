#!/usr/bin/env python3
"""Benchmark preprocessing of INANNA AI source texts."""

from __future__ import annotations

import time
from pathlib import Path

from . import preprocess, source_loader


def main() -> None:
    """Load a subset of texts and time :func:`preprocess.preprocess_texts`."""
    texts = source_loader.load_sources()
    if not texts:
        print("No texts found.")
        return

    subset_items = list(texts.items())[:5]
    subset = dict(subset_items)

    start = time.perf_counter()
    preprocess.preprocess_texts(subset, cache_dir=Path("cache"))
    duration = time.perf_counter() - start

    print(f"Processed {len(subset)} texts in {duration:.2f} seconds")


if __name__ == "__main__":
    main()
