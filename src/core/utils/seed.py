"""Utilities for deterministic behaviour."""

from __future__ import annotations

import random

import numpy as np

try:  # pragma: no cover - optional dependency
    import torch
except Exception:  # pragma: no cover - torch not installed
    torch = None  # type: ignore


def seed_all(seed: int) -> None:
    """Seed Python, NumPy and PyTorch random number generators."""
    random.seed(seed)
    if hasattr(np, "random") and hasattr(np.random, "seed"):
        np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        if (
            hasattr(torch, "cuda") and torch.cuda.is_available()
        ):  # pragma: no cover - gpu
            torch.cuda.manual_seed_all(seed)


__all__ = ["seed_all"]
