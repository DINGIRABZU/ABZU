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

    def set_status(self, _status) -> None:  # pragma: no cover - behaviourless shim
        return None

    def record_exception(self, _exc: BaseException) -> None:  # pragma: no cover
        return None

    def add_event(
        self,
        _name: str,
        attributes: dict[str, object] | None = None,
        **_kwargs,
    ) -> None:  # pragma: no cover
        return None


class _DummyTracer:
    """Tracer returning inert spans for test usage."""

    @contextmanager
    def start_as_current_span(self, _name: str, **_ignored) -> Iterator[_DummySpan]:
        span = _DummySpan()
        try:
            yield span
        finally:
            pass


def get_tracer(_name: str) -> _DummyTracer:
    """Return a no-op tracer implementation."""

    return _DummyTracer()


__all__ = ["get_tracer"]
