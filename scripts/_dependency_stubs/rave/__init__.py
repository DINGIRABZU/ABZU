"""Simplified :mod:`rave` interface used during rehearsals when the real
implementation is unavailable."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as _np
import torch

__all__ = ["RAVE", "__version__", "__ABZU_FALLBACK__"]

__version__ = "0.0.0-stub"
__ABZU_FALLBACK__ = True


@dataclass
class RAVE:
    """Minimal codec preserving the encode/decode API of the real package."""

    checkpoint: Path | str
    device: str = "cpu"

    def __post_init__(self) -> None:
        self.checkpoint = Path(self.checkpoint)
        self.device = str(self.device)

    def _tensor(self, value: Any) -> torch.Tensor:
        tensor = value if isinstance(value, torch.Tensor) else torch.as_tensor(value)
        return tensor.to(self.device, dtype=torch.float32)

    def encode(self, audio: Any) -> torch.Tensor:
        tensor = self._tensor(audio)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        return tensor.clone()

    def decode(self, latents: Any) -> torch.Tensor:
        tensor = self._tensor(latents)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        return tensor.clone()


def _ensure_imports() -> None:  # pragma: no cover - defensive guard
    """Ensure NumPy arrays convert cleanly through the tensor shim."""

    if not hasattr(torch, "as_tensor"):
        raise RuntimeError("torch fallback missing as_tensor helper")
    _ = torch.as_tensor(_np.zeros(1, dtype=_np.float32))


_ensure_imports()
