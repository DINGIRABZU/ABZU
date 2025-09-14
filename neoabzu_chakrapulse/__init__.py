"""Test stub for neoabzu_chakrapulse crate."""

from __future__ import annotations

from typing import Iterator

__all__ = ["emit_pulse", "subscribe_chakra"]


def emit_pulse(source: str, ok: bool) -> None:
    """Pretend to emit a ChakraPulse heartbeat."""
    return None


class _DummyRx:
    def iter(self) -> Iterator[str]:
        return iter(())


def subscribe_chakra() -> _DummyRx:
    """Return an object with an ``iter`` method yielding no pulses."""
    return _DummyRx()
