"""Registry and launcher for auxiliary language models."""

from __future__ import annotations

import asyncio
import threading
from typing import Awaitable, Callable, Dict, List, cast

from tools import kimi_k2_client

_Handler = Callable[[str], Awaitable[str] | str]
_REGISTRY: Dict[str, _Handler] = {}
_LOCK = threading.Lock()


def register_model(name: str, handler: _Handler) -> None:
    """Register ``handler`` under ``name``."""
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
    result = handler(prompt)
    if asyncio.iscoroutine(result):
        return await result
    return cast(str, result)


def invoke_sync(name: str, prompt: str) -> str:
    """Invoke ``name`` with ``prompt`` synchronously."""
    return asyncio.run(invoke(name, prompt))


__all__ = [
    "register_model",
    "register_subprocess_model",
    "invoke",
    "invoke_sync",
    "list_models",
    "has_model",
    "register_kimi_k2",
]
