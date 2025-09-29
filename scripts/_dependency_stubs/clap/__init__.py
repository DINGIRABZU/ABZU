"""Fallback implementation of the :mod:`clap` package."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ClapModel",
    "ClapProcessor",
    "get_version",
    "__version__",
    "__ABZU_FALLBACK__",
]

__version__ = "0.0.0-stub"
__ABZU_FALLBACK__ = True


class _Unavailable:
    """Base class raising informative errors for stubbed access."""

    name: str = "clap"

    @classmethod
    def from_pretrained(cls, *_args: Any, **_kwargs: Any) -> "_Unavailable":
        raise RuntimeError(
            f"{cls.name} unavailable: clap fallback stub active during rehearsal"
        )

    def __call__(self, *_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(
            f"{self.name} unavailable: clap fallback stub active during rehearsal"
        )


class ClapModel(_Unavailable):
    """Placeholder that matches the transformer CLAP API surface."""

    name = "ClapModel"


class ClapProcessor(_Unavailable):
    """Placeholder processor mirroring :class:`transformers.ClapProcessor`."""

    name = "ClapProcessor"


def get_version() -> str:
    """Return the stub description used in diagnostics."""

    return "clap-fallback-stub"
