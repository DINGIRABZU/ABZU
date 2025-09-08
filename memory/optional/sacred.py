"""No-op sacred glyph generator when torch or Pillow are unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from pathlib import Path
from typing import Dict, Iterable, Tuple

SACRED_DIR = Path("data/sacred")


class SacredVAE:  # pragma: no cover - placeholder stub
    """Placeholder VAE returning empty artifacts."""

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - stub
        pass


def generate_sacred_glyph(inputs: Dict[str, Iterable[float]]) -> Tuple[Path, str]:
    """Return an empty path and phrase when sacred dependencies are missing."""

    return Path(), ""


__all__ = ["generate_sacred_glyph", "SacredVAE", "SACRED_DIR"]
