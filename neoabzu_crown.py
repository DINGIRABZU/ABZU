"""Fallback stub for neoabzu_crown load_identity bindings."""

from __future__ import annotations

from identity_loader import load_identity as _load_identity


def load_identity(integration):  # pragma: no cover - simple proxy
    return _load_identity(integration)


__all__ = ["load_identity"]
