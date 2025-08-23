"""Helpers for optional dependencies with lightweight stubs."""

from __future__ import annotations

import logging
import random as _random
import types
from importlib import import_module
from typing import Any, Callable, Dict, List, Sequence, cast

logger = logging.getLogger(__name__)


def _stub_numpy() -> Any:
    """Return a very small subset of the NumPy API."""

    def zeros(shape: int | tuple[int, ...], dtype: type[float] = float) -> List[float]:
        size = shape[0] if isinstance(shape, tuple) else int(shape)
        return [dtype(0)] * size

    def clip(x: float | Sequence[float], a: float, b: float) -> float | List[float]:
        if isinstance(x, (list, tuple)):
            return [max(a, min(b, float(v))) for v in x]
        return max(a, min(b, float(cast(float, x))))

    def _rand(size: int | None = None) -> float | List[float]:
        if size is None:
            return _random.random()
        return [_random.random() for _ in range(size)]

    def _randint(
        low: int, high: int | None = None, size: int | None = None
    ) -> int | List[int]:
        if high is None:
            high = low
            low = 0

        def _one() -> int:
            return _random.randint(low, high - 1)

        if size is None:
            return _one()
        return [_one() for _ in range(size)]

    def _permutation(x: int | Sequence[int]) -> List[int]:
        arr = list(range(x)) if isinstance(x, int) else list(x)
        _random.shuffle(arr)
        return arr

    def _seed(seed: int | None = None) -> None:
        _random.seed(seed)

    rng = types.SimpleNamespace(
        rand=_rand,
        random=_rand,
        randint=_randint,
        permutation=_permutation,
        seed=_seed,
    )
    return types.SimpleNamespace(float32=float, zeros=zeros, clip=clip, random=rng)


def _stub_gymnasium() -> Any:
    class _Box:
        def __init__(self, *a: Any, **k: Any) -> None:
            pass

    class _Discrete:
        def __init__(self, *a: Any, **k: Any) -> None:
            pass

    class _Env:
        pass

    class _Spaces(types.SimpleNamespace):
        Box = _Box
        Discrete = _Discrete

    return types.SimpleNamespace(Env=_Env, spaces=_Spaces())


def _stub_stable_baselines3() -> Any:
    class _ReplayBuffer:
        def add(self, *a: Any, **k: Any) -> None:
            pass

    class _PPO:
        def __init__(self, *a: Any, **k: Any) -> None:
            pass

        def learn(self, *a: Any, **k: Any) -> None:
            pass

    class _DQN:
        def __init__(self, *a: Any, **k: Any) -> None:
            self.replay_buffer = _ReplayBuffer()

        def learn(self, *a: Any, **k: Any) -> None:
            pass

        def train(self, *a: Any, **k: Any) -> None:
            pass

    return types.SimpleNamespace(PPO=_PPO, DQN=_DQN)


_STUBS: Dict[str, Callable[[], Any]] = {
    "numpy": _stub_numpy,
    "gymnasium": _stub_gymnasium,
    "stable_baselines3": _stub_stable_baselines3,
}


def lazy_import(name: str) -> Any:
    """Return ``name`` if import succeeds, otherwise a lightweight stub.

    The returned module carries ``__stub__ = True`` when a stub is used so
    callers can detect missing optional dependencies.
    """

    try:
        module = import_module(name)
        setattr(module, "__stub__", False)
        return module
    except Exception:  # pragma: no cover - import failure path
        factory = _STUBS.get(name)
        if factory is None:
            logger.debug("optional dependency %s missing", name)
            return types.SimpleNamespace(__stub__=True)
        stub = factory()
        setattr(stub, "__stub__", True)
        return stub


__all__ = ["lazy_import"]
