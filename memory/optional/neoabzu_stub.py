"""Deterministic in-memory stand-in for the :mod:`neoabzu_memory` bundle."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from agents.event_bus import emit_event

__all__ = ["MemoryBundle", "STUBBED_LAYERS", "STUB_IMPLEMENTATION"]


STUB_IMPLEMENTATION = "memory.optional.neoabzu_stub"

STUBBED_LAYERS: Tuple[str, ...] = (
    "cortex",
    "vector",
    "spiral",
    "emotional",
    "mental",
    "spiritual",
    "narrative",
    "core",
)

# Rotating pools provide lightweight, deterministic content for each layer.
_CORTEX_TOPICS: Tuple[str, ...] = (
    "aurora",
    "citadel",
    "echo",
    "glyph",
    "lumen",
    "nocturne",
    "pulse",
    "quartz",
)
_EMOTIONS: Tuple[str, ...] = (
    "calm",
    "focused",
    "curious",
    "hopeful",
    "joyful",
    "reflective",
    "resolute",
    "serene",
)
_MENTAL_TASKS: Tuple[str, ...] = (
    "plan",
    "synthesise",
    "analyse",
    "observe",
    "catalogue",
    "prototype",
    "review",
    "summarise",
)
_SPIRITUAL_SYMBOLS: Tuple[str, ...] = (
    "sigil-alpha",
    "sigil-bright",
    "sigil-crest",
    "sigil-delta",
    "sigil-echo",
    "sigil-flare",
    "sigil-grove",
    "sigil-halo",
)


@dataclass(frozen=True)
class _StubRecord:
    """Pre-generated payload used to satisfy MemoryBundle queries."""

    idx: int
    text: str
    summary: str

    @property
    def tags(self) -> Tuple[str, str]:
        return (f"tag-{self.idx % 17}", f"cluster-{self.idx % 11}")

    @property
    def emotion(self) -> Dict[str, Any]:
        affect = _EMOTIONS[self.idx % len(_EMOTIONS)]
        return {"affect": affect, "confidence": round(0.75, 2)}

    @property
    def mental(self) -> Dict[str, Any]:
        task = _MENTAL_TASKS[self.idx % len(_MENTAL_TASKS)]
        return {"task": task, "relevance": round(0.6 + (self.idx % 5) * 0.05, 2)}

    @property
    def spiritual(self) -> Dict[str, Any]:
        symbol = _SPIRITUAL_SYMBOLS[self.idx % len(_SPIRITUAL_SYMBOLS)]
        return {"symbol": symbol, "meaning": f"insight-{self.idx % 13}"}

    @property
    def narrative(self) -> Dict[str, Any]:
        return {
            "story": f"Stub narrative thread {self.idx}",
            "coherence": round(0.8 + (self.idx % 3) * 0.05, 2),
        }

    @property
    def vector(self) -> Dict[str, Any]:
        base = self.idx % 9973 / 9973
        return {
            "embedding": [
                round(base, 6),
                round((base * 0.5) % 1.0, 6),
                round((base * 0.25) % 1.0, 6),
            ],
            "score": round(0.7 + (self.idx % 7) * 0.02, 3),
            "source": "stub-vector",
        }

    @property
    def cortex(self) -> Dict[str, Any]:
        topic = _CORTEX_TOPICS[self.idx % len(_CORTEX_TOPICS)]
        return {
            "text": self.text,
            "similarity": round(0.65 + (self.idx % 9) * 0.03, 3),
            "source": "stub-cortex",
            "topic": topic,
            "tags": list(self.tags),
        }

    @property
    def spiral(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "resonance": round(0.4 + (self.idx % 6) * 0.07, 3),
        }


class MemoryBundle:
    """Stand-in for the Rust :class:`neoabzu_memory.MemoryBundle` class."""

    fallback_reason = "neoabzu_memory_unavailable"
    implementation = STUB_IMPLEMENTATION

    def __init__(
        self,
        import_error: BaseException | None = None,
        *,
        item_count: int = 10_000,
    ) -> None:
        self._import_error = import_error
        self._item_count = max(int(item_count), 1)
        self._initialized = False
        self.stubbed = True
        self.statuses: Dict[str, str] = {}
        self.diagnostics: Dict[str, Dict[str, Any]] = {}
        self._records = tuple(self._build_record(i) for i in range(self._item_count))

    def _build_record(self, index: int) -> _StubRecord:
        text = f"Stub memory record {index}"
        summary = f"Stub spiral echo for record {index}"
        return _StubRecord(idx=index, text=text, summary=summary)

    def _select_record(self, text: str) -> _StubRecord:
        digest = hashlib.blake2b(
            text.encode("utf-8"), digest_size=4, person=b"neoabzu_stub"
        ).digest()
        index = int.from_bytes(digest, "big") % len(self._records)
        return self._records[index]

    def _build_attempts(self) -> list[Dict[str, Any]]:
        error_text = (
            repr(self._import_error)
            if self._import_error is not None
            else "module_not_found"
        )
        return [
            {
                "module": "neoabzu_memory",
                "outcome": "error",
                "error": error_text,
            },
            {
                "module": STUB_IMPLEMENTATION,
                "outcome": "loaded",
            },
        ]

    def initialize(self) -> Dict[str, Any]:
        """Return deterministic statuses and diagnostics for each layer."""

        attempts = self._build_attempts()
        statuses = {layer: "skipped" for layer in STUBBED_LAYERS}
        diagnostics = {
            layer: {
                "status": "skipped",
                "fallback_reason": self.fallback_reason,
                "loaded_module": STUB_IMPLEMENTATION,
                "attempts": [dict(entry) for entry in attempts],
            }
            for layer in STUBBED_LAYERS
        }
        diagnostics["__bundle__"] = {
            "implementation": STUB_IMPLEMENTATION,
            "stubbed": True,
            "fallback_reason": self.fallback_reason,
            "attempts": [dict(entry) for entry in attempts],
        }

        emit_event("memory", "layer_init", {"layers": dict(statuses)})

        self.statuses = statuses
        self.diagnostics = diagnostics
        self._initialized = True
        return {
            "statuses": dict(statuses),
            "diagnostics": {
                key: {
                    **value,
                    "attempts": [dict(entry) for entry in value.get("attempts", [])],
                }
                for key, value in diagnostics.items()
            },
            "stubbed": True,
            "fallback_reason": self.fallback_reason,
            "implementation": STUB_IMPLEMENTATION,
        }

    def query(self, text: str) -> Dict[str, Any]:
        """Return deterministic memory results derived from ``text``."""

        if not self._initialized:
            self.initialize()

        record = self._select_record(text)
        return {
            "cortex": [record.cortex],
            "vector": [record.vector],
            "spiral": record.spiral,
            "emotional": [record.emotion],
            "mental": [record.mental],
            "spiritual": [record.spiritual],
            "narrative": [record.narrative],
            "core": f"stub-core-{record.idx}",
            "failed_layers": [],
            "stubbed": True,
            "implementation": STUB_IMPLEMENTATION,
        }
