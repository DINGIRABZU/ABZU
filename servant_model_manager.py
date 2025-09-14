"""Registry and launcher for auxiliary language models."""

from __future__ import annotations

import asyncio
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, cast

from tools import kimi_k2_client, opencode_client

_Handler = Callable[[str], Awaitable[str] | str]
_REGISTRY: Dict[str, _Handler] = {}
_LOCK = threading.Lock()


@dataclass
class _Pulse:
    """Simple pulse metrics for servant models."""

    latencies: deque[float] = field(default_factory=lambda: deque(maxlen=10))
    calls: int = 0
    failures: int = 0


_PULSES: Dict[str, _Pulse] = defaultdict(_Pulse)


def register_model(name: str, handler: _Handler) -> None:
    """Register ``handler`` under ``name``."""
    with _LOCK:
        _REGISTRY[name] = handler


def unregister_model(name: str) -> None:
    """Remove ``name`` from the registry if present."""
    with _LOCK:
        _REGISTRY.pop(name, None)


def reload_model(name: str, handler: _Handler) -> None:
    """Replace ``name`` with ``handler``, registering if absent."""
    with _LOCK:
        _REGISTRY[name] = handler


def register_subprocess_model(name: str, command: List[str]) -> None:
    """Register a model invoked via subprocess ``command``."""

    async def _run(prompt: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        assert proc.stdin is not None
        assert proc.stdout is not None
        out, _ = await proc.communicate(prompt.encode())
        return out.decode().strip()

    register_model(name, _run)


def register_kimi_k2() -> None:
    """Register the Kimi-K2 servant model."""
    register_model("kimi_k2", kimi_k2_client.complete)


def register_opencode() -> None:
    """Register the Opencode servant model."""
    register_model("opencode", opencode_client.complete)


def has_model(name: str) -> bool:
    """Return ``True`` if ``name`` is registered."""
    with _LOCK:
        return name in _REGISTRY


def list_models() -> List[str]:
    """Return registered model names."""
    with _LOCK:
        return list(_REGISTRY)


async def invoke(name: str, prompt: str) -> str:
    """Invoke the model ``name`` with ``prompt``."""
    with _LOCK:
        handler = _REGISTRY.get(name)
    if handler is None:
        raise KeyError(name)
    start = time.perf_counter()
    success = False
    try:
        result = handler(prompt)
        if asyncio.iscoroutine(result):
            result = await result
        success = True
        return cast(str, result)
    finally:
        elapsed = time.perf_counter() - start
        pulse = _PULSES[name]
        pulse.calls += 1
        pulse.latencies.append(elapsed)
        if not success:
            pulse.failures += 1


def invoke_sync(name: str, prompt: str) -> str:
    """Invoke ``name`` with ``prompt`` synchronously."""
    return asyncio.run(invoke(name, prompt))


def pulse_metrics(name: str) -> Dict[str, float]:
    """Return average latency and failure rate for ``name``."""
    pulse = _PULSES.get(name)
    if not pulse or pulse.calls == 0:
        return {"avg_latency": 0.0, "failure_rate": 0.0}
    avg_latency = sum(pulse.latencies) / len(pulse.latencies)
    failure_rate = pulse.failures / pulse.calls
    return {"avg_latency": avg_latency, "failure_rate": failure_rate}


__all__ = [
    "register_model",
    "unregister_model",
    "reload_model",
    "register_subprocess_model",
    "invoke",
    "invoke_sync",
    "list_models",
    "has_model",
    "register_kimi_k2",
    "register_opencode",
    "pulse_metrics",
]
