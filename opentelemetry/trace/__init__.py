"""Test stub for :mod:`opentelemetry.trace` used in lightweight spans."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


class _DummySpan:
    """Context manager mimicking a span interface."""

    def __enter__(self) -> "_DummySpan":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def set_attribute(self, _key: str, _value: object) -> None:
        return None


class _DummyTracer:
    """Tracer returning inert spans for test usage."""

    @contextmanager
    def start_as_current_span(self, _name: str) -> Iterator[_DummySpan]:
        span = _DummySpan()
        try:
            yield span
        finally:
            pass


def get_tracer(_name: str) -> _DummyTracer:
    """Return a no-op tracer implementation."""

    return _DummyTracer()


__all__ = ["get_tracer"]
