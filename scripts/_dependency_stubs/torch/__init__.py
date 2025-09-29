"""Minimal :mod:`torch` fallback to satisfy Stage B rehearsal imports."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any, Iterator

import numpy as _np

__all__ = [
    "Tensor",
    "as_tensor",
    "from_numpy",
    "no_grad",
    "tensor",
    "float32",
    "__version__",
    "__ABZU_FALLBACK__",
]

__version__ = "0.0.0-stub"
__ABZU_FALLBACK__ = True

float32 = _np.float32


@dataclass
class Tensor:
    """Lightweight tensor wrapper used by the rehearsal fallbacks."""

    _array: _np.ndarray

    def __init__(self, data: Any, *, dtype: Any | None = None) -> None:
        array = _np.array(data, dtype=dtype or _np.float32, copy=False)
        if array.dtype.kind not in {"f", "i", "u"}:
            array = array.astype(_np.float32)
        object.__setattr__(self, "_array", array)

    # ------------------------------------------------------------------
    # Torch-like helpers
    # ------------------------------------------------------------------
    def detach(self) -> "Tensor":
        return Tensor(self._array.copy())

    def clone(self) -> "Tensor":
        return Tensor(self._array.copy())

    def unsqueeze(self, dim: int) -> "Tensor":
        return Tensor(_np.expand_dims(self._array, axis=dim))

    def squeeze(self, axis: int | None = None) -> "Tensor":
        return Tensor(_np.squeeze(self._array, axis=axis))

    def to(self, *_args: Any, dtype: Any | None = None, **_kwargs: Any) -> "Tensor":
        if dtype is not None:
            return Tensor(self._array.astype(dtype))
        return self

    def cpu(self) -> "Tensor":
        return self

    def numpy(self) -> _np.ndarray:
        return _np.array(self._array, copy=True)

    def dim(self) -> int:
        return int(self._array.ndim)

    # ------------------------------------------------------------------
    # NumPy compatibility
    # ------------------------------------------------------------------
    def __array__(self, dtype: Any | None = None) -> _np.ndarray:
        if dtype is None:
            return _np.array(self._array, copy=True)
        return _np.array(self._array, copy=True).astype(dtype)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._array)

    def __len__(self) -> int:
        return int(self._array.shape[0]) if self._array.ndim else 1

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Tensor(shape={self._array.shape}, dtype={self._array.dtype})"


def as_tensor(data: Any, *, dtype: Any | None = None) -> Tensor:
    return Tensor(data, dtype=dtype)


def from_numpy(array: _np.ndarray) -> Tensor:
    return Tensor(_np.array(array, copy=False))


def tensor(data: Any, dtype: Any | None = None) -> Tensor:
    return Tensor(data, dtype=dtype)


@contextlib.contextmanager
def no_grad() -> Iterator[None]:  # pragma: no cover - trivial helper
    yield
