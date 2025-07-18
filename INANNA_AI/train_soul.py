from __future__ import annotations

"""Utilities for fine-tuning the :class:`RFA7D` core."""

import argparse
import hashlib
from pathlib import Path

import numpy as np

from .rfa_7d import RFA7D


def fractal_mutate(core: RFA7D, seed: int) -> None:
    """Apply a simple fractal-like mutation to ``core``."""
    rng = np.random.default_rng(seed)
    mutation = rng.standard_normal(core.shape) * 0.01
    core.grid += mutation
    if not core.verify_integrity():
        core.integrity_hash = hashlib.sha3_256(core.grid.tobytes()).hexdigest()


def train_soul(log_path: Path, iterations: int = 3) -> None:
    """Update ``RFA7D`` using interaction logs then write ``soul.dna``."""
    text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    core = RFA7D()
    for i in range(iterations):
        fractal_mutate(core, seed=len(text) + i)
    core.encode_to_dna()


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI entry
    parser = argparse.ArgumentParser(description="Fine-tune the RFA7D soul grid")
    parser.add_argument("log", help="Path to interaction log")
    parser.add_argument("--iterations", type=int, default=3, help="Number of updates")
    args = parser.parse_args(argv)
    train_soul(Path(args.log), args.iterations)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()

