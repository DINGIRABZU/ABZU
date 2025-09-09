from __future__ import annotations

import os
from importlib import import_module
from typing import Any, Callable

__version__ = "0.1.0"


class NoOpSpan:
    def __enter__(self) -> "NoOpSpan":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False

    def set_attribute(
        self, *args: Any, **kwargs: Any
    ) -> None:  # pragma: no cover - no-op
        pass


class NoOpTracer:
    def start_as_current_span(
        self, *_: Any, **__: Any
    ) -> NoOpSpan:  # pragma: no cover - no-op
        return NoOpSpan()


def _load_custom(provider: str, name: str) -> Any:
    module_path, func_name = provider.split(":", 1)
    module = import_module(module_path)
    factory: Callable[[str], Any] = getattr(module, func_name)
    return factory(name)


def get_tracer(name: str) -> Any:
    """Return a tracer instance based on ``TRACE_PROVIDER``."""
    provider = os.getenv("TRACE_PROVIDER", "noop").lower()

    if provider == "opentelemetry":
        try:  # pragma: no cover - optional dependency
            from opentelemetry import trace

            return trace.get_tracer(name)
        except Exception:  # pragma: no cover - fallback to noop on error
            return NoOpTracer()
    if provider == "noop":
        return NoOpTracer()
    if ":" in provider:
        try:
            return _load_custom(provider, name)
        except Exception:  # pragma: no cover - fallback to noop on error
            return NoOpTracer()
    return NoOpTracer()


__all__ = ["get_tracer"]
