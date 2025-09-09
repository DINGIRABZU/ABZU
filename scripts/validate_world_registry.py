#!/usr/bin/env python3
"""Validate world registry entries against existing components."""

from __future__ import annotations

from pathlib import Path
import sys
import types
from types import ModuleType
from typing import Any, Dict, Literal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class _DummySpan:
    def __enter__(self) -> "_DummySpan":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> Literal[False]:
        return False

    def set_attribute(self, *args: object, **kwargs: object) -> None:
        return None


def _ensure_tracer_stub() -> None:
    """Provide a minimal opentelemetry stub if missing."""
    if "opentelemetry" in sys.modules:
        return
    tracer = types.SimpleNamespace(start_as_current_span=lambda *a, **k: _DummySpan())
    stub = ModuleType("opentelemetry")
    stub.trace = types.SimpleNamespace(get_tracer=lambda *a, **k: tracer)  # type: ignore[attr-defined]
    sys.modules["opentelemetry"] = stub


_ensure_tracer_stub()

from worlds.config_registry import export_config  # noqa: E402

__version__ = "0.1.0"


def _load_registry() -> Dict[str, Any]:
    """Populate and return the configuration registry."""
    # Import modules that register layers and agents on import.
    import agents  # noqa: F401
    import memory  # noqa: F401

    return export_config()


def main() -> int:
    """Return 0 when registry entries match existing components."""
    config: Dict[str, Any] = _load_registry()
    errors: list[str] = []

    for layer in config.get("layers", []):
        candidates = [ROOT / "memory" / f"{layer}.py", ROOT / "memory" / layer]
        if layer == "narrative":
            candidates.append(ROOT / "memory" / "narrative_engine.py")
        if layer == "vector":
            candidates.append(ROOT / "vector_memory.py")
        if layer == "spiral":
            candidates.append(ROOT / "spiral_memory.py")
        if not any(p.exists() for p in candidates):
            errors.append(f"Unknown layer: {layer}")

    for agent in config.get("agents", []):
        if not (ROOT / "agents" / agent).is_dir():
            errors.append(f"Unknown agent: {agent}")

    if errors:
        print("World registry validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
