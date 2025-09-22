"""Minimal RAVE compatibility layer for rehearsal DSP helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

__all__ = ["RAVE", "__version__"]

__version__ = "0.1.0"


@dataclass
class RAVE:
    """Stateless shim mirroring the public API of the original package."""

    checkpoint: Path | str
    device: str = "cpu"

    def __post_init__(self) -> None:
        self.checkpoint = Path(self.checkpoint)
        self.device = str(self.device)

    def _as_tensor(self, value: Any) -> torch.Tensor:
        tensor = value if isinstance(value, torch.Tensor) else torch.as_tensor(value)
        return tensor.to(self.device, dtype=torch.float32)

    def encode(self, audio: torch.Tensor) -> torch.Tensor:
        """Return a latent representation for ``audio``."""

        tensor = self._as_tensor(audio)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        return tensor.detach().clone()

    def decode(self, latents: torch.Tensor) -> torch.Tensor:
        """Synthesize audio samples from ``latents``."""

        tensor = self._as_tensor(latents)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        return tensor.detach().clone()
