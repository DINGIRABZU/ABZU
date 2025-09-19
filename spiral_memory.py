"""Cross-layer spiral memory with recursive recall and event registry.

Maintains multi-layer event history and offers mechanisms for spiral-style
retrieval across different cognitive levels.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Mapping, Sequence

from opentelemetry import trace
from memory.sacred import generate_sacred_glyph

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)

try:  # pragma: no cover - optional dependency
    import torch
    import torch.nn as nn
except Exception as exc:  # pragma: no cover - optional dependency
    logger.exception("optional torch dependency failed to import: %s", exc)
    torch = None  # type: ignore
    nn = None  # type: ignore

REGISTRY_DB = Path("data/spiral_registry.db")


def _connect(db_path: Path) -> sqlite3.Connection:
    """Return SQLite connection ensuring the events table exists."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event TEXT,
            glyph_path TEXT,
            phrase TEXT
        )
        """
    )
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
        if "glyph_path" not in cols:
            conn.execute("ALTER TABLE events ADD COLUMN glyph_path TEXT")
        if "phrase" not in cols:
            conn.execute("ALTER TABLE events ADD COLUMN phrase TEXT")
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("failed to ensure event table schema: %s", exc)
    return conn


@dataclass
class RecursiveTransformer:  # pragma: no cover - simple demo network
    """Tiny recursive transformer used when ``torch`` is available."""

    width: int
    depth: int = 2
    model: nn.TransformerEncoder | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        if torch is None or nn is None:
            return
        layer = nn.TransformerEncoderLayer(self.width, nhead=2)
        self.model = nn.TransformerEncoder(layer, num_layers=self.depth)

    def __call__(self, data: torch.Tensor) -> torch.Tensor:
        if self.model is None:
            raise RuntimeError("torch not available")
        return self.model(data)


@dataclass
class SpiralMemory:
    """Store layer-wise memories and major events."""

    db_path: Path = REGISTRY_DB
    width: int = 16
    layers: List[Sequence[float]] = field(default_factory=list)
    _model: RecursiveTransformer | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        if torch is not None:
            self._model = RecursiveTransformer(self.width)

    # ------------------------------------------------------------------ layers
    def add_layer(self, data: Sequence[float]) -> None:
        """Append ``data`` as a memory layer."""

        self.layers.append(data)

    def aggregate(self) -> List[float]:
        """Return the cross-layer aggregate."""

        if not self.layers:
            return []
        if torch is not None and self._model is not None:
            tensor = torch.tensor(self.layers, dtype=torch.float32)
            result = self._model(tensor)
            return result.mean(dim=0).tolist()
        length = max(len(layer) for layer in self.layers)
        acc: List[List[float]] = [[] for _ in range(length)]
        for layer in self.layers:
            for idx, val in enumerate(layer):
                acc[idx].append(float(val))
        return [mean(values) for values in acc]

    # ------------------------------------------------------------ event loggers
    def register_event(
        self, event: str, layers: Mapping[str, Iterable[float]] | None = None
    ) -> None:
        """Record a major event in the fractal registry.

        Parameters
        ----------
        event:
            Description of the event.
        layers:
            Optional mapping of layer embeddings to generate a sacred glyph.
        """

        glyph_path: str | None = None
        phrase: str | None = None
        if layers:
            try:
                path, phrase = generate_sacred_glyph(layers)
                glyph_path = str(path)
            except Exception as exc:  # pragma: no cover - best effort
                logger.exception("glyph generation failed: %s", exc)

        with _connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO events (timestamp, event, glyph_path, "
                    "phrase) VALUES (?, ?, ?, ?)"
                ),
                (datetime.utcnow().isoformat(), event, glyph_path, phrase),
            )

    def _load_events(self, limit: int = 50) -> List[tuple[str, str | None, str | None]]:
        with _connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT event, glyph_path, phrase FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [(row[0], row[1], row[2]) for row in cur.fetchall()]

    # ----------------------------------------------------------------- recall
    def recall(self, query: str) -> str:
        """Return a synthesized insight for ``query``."""
        with _tracer.start_as_current_span("spiral_memory.recall") as span:
            span.set_attribute("spiral_memory.query", query)

            events = self._load_events()
            agg = self.aggregate()
            parts: List[str] = []
            for event, glyph, phrase in events:
                extras = [e for e in (glyph, phrase) if e]
                if extras:
                    parts.append(f"{event} ({' | '.join(extras)})")
                else:
                    parts.append(event)
            insight = " | ".join(parts)
            if agg:
                vector = ", ".join(f"{v:.2f}" for v in agg)
                insight = f"{insight} || signal [{vector}]"
            return f"{query}: {insight}" if insight else f"{query}: (no data)"


DEFAULT_MEMORY = SpiralMemory()


def spiral_recall(query: str) -> str:
    """Expose :class:`SpiralMemory` recall via module-level function."""

    return DEFAULT_MEMORY.recall(query)


__all__ = ["SpiralMemory", "spiral_recall", "REGISTRY_DB"]
