# Patent pending – see PATENTS.md
"""Thin wrapper around the Rust memory bundle."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable

from memory.tracing import get_tracer

__version__ = "0.2.0"


logger = logging.getLogger("memory.bundle")


@lru_cache(maxsize=1)
def _bundle_search_roots() -> tuple[Path, ...]:
    """Return directories that may contain the compiled bundle."""

    roots: list[Path] = []
    env_override = os.getenv("NEOABZU_MEMORY_LIB_DIR")
    if env_override:
        override = Path(env_override).resolve()
        roots.append(override)

    current = Path(__file__).resolve()
    for candidate in [current, *current.parents]:
        release_dir = candidate / "target" / "release"
        if release_dir.exists():
            roots.append(release_dir)
            deps_dir = release_dir / "deps"
            if deps_dir.exists():
                roots.append(deps_dir)

    seen: set[Path] = set()
    ordered: list[Path] = []
    for directory in roots:
        if directory.exists():
            resolved = directory.resolve()
            if resolved not in seen:
                seen.add(resolved)
                ordered.append(resolved)
    return tuple(ordered)


def _iter_bundle_candidates(name: str) -> Iterable[Path]:
    """Yield possible extension artifacts for ``name``."""

    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    prefixes = ("", "lib")
    for directory in _bundle_search_roots():
        for prefix in prefixes:
            for suffix in suffixes:
                candidate = directory / f"{prefix}{name}{suffix}"
                if candidate.exists() and candidate.is_file():
                    yield candidate
        # Fall back to globbing for suffixed filenames (e.g. abi3 wheels).
        for suffix in suffixes:
            for prefix in prefixes:
                pattern = f"{prefix}{name}*{suffix}"
                for candidate in sorted(directory.glob(pattern)):
                    if candidate.is_file():
                        yield candidate


def _load_extension_module(name: str, path: Path):
    """Load ``name`` from ``path`` using the extension loader."""

    loader = importlib.machinery.ExtensionFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise ImportError(f"Unable to create module spec for {name} at {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    sys.modules[name] = module
    return module


def _import_native_bundle() -> tuple[type[Any] | None, ImportError | None, Path | None]:
    """Attempt to import the compiled Neo‑ABZU bundle."""

    try:
        from neoabzu_memory import MemoryBundle as bundle  # type: ignore

    except (ModuleNotFoundError, ImportError) as exc:
        last_error: ImportError | None = None
        for candidate in _iter_bundle_candidates("neoabzu_memory"):
            try:
                module = _load_extension_module("neoabzu_memory", candidate)
            except Exception as load_exc:  # pragma: no cover - loader errors vary
                logger.debug(
                    "Failed to load neoabzu_memory extension",  # pragma: no cover
                    extra={"candidate": str(candidate)},
                    exc_info=load_exc,
                )
                last_error = ImportError(
                    f"neoabzu_memory extension at {candidate} failed to load"
                )
                last_error.__cause__ = load_exc
                continue
            bundle = getattr(module, "MemoryBundle", None)
            if bundle is None:
                last_error = ImportError(
                    f"neoabzu_memory extension at {candidate} missing MemoryBundle"
                )
                continue
            logger.info(
                "neoabzu_memory extension loaded",
                extra={"bundle_path": str(candidate)},
            )
            return bundle, None, candidate
        if last_error is not None:
            return None, last_error, None
        message = (
            "neoabzu_memory extension not found. Run "
            "'cargo build -p neoabzu-memory --release' on the host to "
            "compile the bundle."
        )
        error = ImportError(message)
        error.__cause__ = exc
        return None, error, None
    else:
        return bundle, None, None


_NeoBundle_cls, _IMPORT_ERROR, _BUNDLE_ARTIFACT = _import_native_bundle()
if _NeoBundle_cls is not None:

    def _bundle_factory() -> Any:
        return _NeoBundle_cls()

    _BUNDLE_SOURCE = "neoabzu_memory"
    _BUNDLE_MODE = "native"
else:
    from memory.optional.neoabzu_bundle import MemoryBundle as _StubBundle

    _BUNDLE_SOURCE = "memory.optional.neoabzu_bundle"
    _BUNDLE_MODE = "stubbed"

    def _bundle_factory() -> Any:
        return _StubBundle(import_error=_IMPORT_ERROR)


class MemoryBundle:
    """Proxy class delegating to the Rust implementation."""

    def __init__(self) -> None:
        self._bundle = _bundle_factory()
        self._tracer = get_tracer(__name__)
        self.bundle_source: str = getattr(
            self._bundle, "bundle_source", _BUNDLE_SOURCE
        )
        self.bundle_mode: str = getattr(self._bundle, "bundle_mode", _BUNDLE_MODE)
        self.stubbed: bool = bool(getattr(self._bundle, "stubbed", False)) or (
            self.bundle_mode == "stubbed"
        )
        self.fallback_reason: str | None = getattr(
            self._bundle, "fallback_reason", None
        )
        if _IMPORT_ERROR is not None:
            logger.warning(
                "neoabzu_memory unavailable – using stub bundle",
                extra={
                    "bundle_source": _BUNDLE_SOURCE,
                    "bundle_mode": _BUNDLE_MODE,
                    "error": repr(_IMPORT_ERROR),
                },
            )
        self.statuses: Dict[str, str] = {}
        self.diagnostics: Dict[str, Any] = {}

    def initialize(self) -> Dict[str, str]:
        """Initialize memory layers through the Rust bundle.

        Returns
        -------
        Dict[str, str]
            Mapping of layer names to their initialization status. Detailed
            diagnostic metadata emitted by the Rust extension (including import
            attempts, fallback selections, and failure reasons) is stored on
            :attr:`diagnostics` for callers that need richer introspection.
        """

        result = self._bundle.initialize()
        statuses = dict(result.get("statuses", {}))
        diagnostics_raw = result.get("diagnostics", {})
        diagnostics: Dict[str, Any] = {}
        optional_fallbacks: list[tuple[str, Dict[str, Any]]] = []
        for layer, info in diagnostics_raw.items():
            entry = dict(info)
            attempts = [dict(attempt) for attempt in entry.get("attempts", [])]
            entry["attempts"] = attempts
            diagnostics[layer] = entry
            loaded_module = entry.get("loaded_module")
            if isinstance(loaded_module, str) and loaded_module.startswith(
                "memory.optional."
            ):
                optional_fallbacks.append((layer, entry))
        bundle_source = result.get("bundle_source")
        if isinstance(bundle_source, str):
            self.bundle_source = bundle_source
        bundle_mode = result.get("bundle_mode")
        if isinstance(bundle_mode, str):
            self.bundle_mode = bundle_mode
        self.statuses = statuses
        self.diagnostics = diagnostics
        self.stubbed = bool(result.get("stubbed", self.stubbed)) or (
            self.bundle_mode == "stubbed"
        )
        if self.stubbed:
            for layer in statuses:
                statuses[layer] = "skipped"
        self.fallback_reason = result.get("fallback_reason", self.fallback_reason)
        if optional_fallbacks:
            summary_pairs = []
            for layer, entry in optional_fallbacks:
                module = entry.get("loaded_module")
                summary_pairs.append(f"{layer}:{module}")
                logger.warning(
                    "Optional memory stub activated",
                    extra={
                        "memory_layer": layer,
                        "fallback_module": module,
                        "fallback_reason": entry.get("fallback_reason"),
                        "layer_status": entry.get("status"),
                    },
                )
            logger.warning(
                "Optional memory modules loaded during initialization",
                extra={
                    "optional_layers": [layer for layer, _ in optional_fallbacks],
                    "optional_modules": [
                        entry.get("loaded_module") for _, entry in optional_fallbacks
                    ],
                    "optional_summary": ", ".join(summary_pairs),
                },
            )
        return statuses

    def query(self, text: str) -> Dict[str, Any]:
        """Aggregate memory queries via the Rust bundle."""
        return self._bundle.query(text)


__all__ = ["MemoryBundle"]
