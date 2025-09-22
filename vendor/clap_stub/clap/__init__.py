"""Compatibility shim exposing CLAP helpers from :mod:`transformers`."""

from __future__ import annotations

__all__ = ["ClapModel", "ClapProcessor", "get_version", "__version__"]

try:  # pragma: no cover - pass-through import
    from transformers import ClapModel, ClapProcessor  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "transformers must provide ClapModel/ClapProcessor for clap shim"
    ) from exc

__version__ = "0.7.1.post1"


def get_version() -> str:
    """Return a descriptive version string for diagnostics."""

    return f"transformers-{ClapModel.__module__}"  # pragma: no cover - trivial
