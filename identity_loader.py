"""Identity loading pipeline for Crown boot."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except ImportError:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]

vector_memory = _vector_memory


MISSION_DOC = Path("docs/project_mission_vision.md")
"""Primary mission document consumed by the identity loader."""

PERSONA_DOC = Path("docs/persona_api_guide.md")
"""Persona reference used for identity bootstrapping."""

IDENTITY_FILE = Path("data/identity.json")
"""Persisted identity summary produced during initialization."""


class _Parser:
    def load_inputs(self, directory: Path) -> List[dict[str, str]]:
        texts: List[dict[str, str]] = []
        for path in sorted(directory.glob("*.md")):
            texts.append(
                {"text": path.read_text(encoding="utf-8"), "source_path": str(path)}
            )
        return texts


parser = _Parser()


class _Embedder:
    def embed_chunks(self, chunks: Sequence[dict[str, str]]) -> List[dict[str, object]]:
        embedded: List[dict[str, object]] = []
        for chunk in chunks:
            embedded.append(
                {
                    "text": chunk["text"],
                    "source_path": chunk["source_path"],
                    "embedding": [0.0],
                }
            )
        return embedded


embedder = _Embedder()


def update_insights(
    entries: Iterable[dict[str, object]]
) -> None:  # pragma: no cover - stub
    """Persist identity insight metadata (stub for monkeypatched tests)."""


def _load_source(directory: Path) -> List[dict[str, str]]:
    if not directory.exists():
        return []
    return parser.load_inputs(directory)


def _store_vectors(chunks: Sequence[dict[str, object]]) -> None:
    if vector_memory is None:
        return
    add_vectors = getattr(vector_memory, "add_vectors", None)
    if not callable(add_vectors):
        return
    texts = [c.get("text", "") for c in chunks]
    metadata = []
    for chunk in chunks:
        metadata.append(
            {
                "source_path": chunk.get("source_path"),
                "type": "identity_source",
                "stage": "crown_boot",
            }
        )
    add_vectors(texts, metadata)


def load_identity(glm: object) -> str:
    """Return cached or newly generated identity summary."""

    if IDENTITY_FILE.exists():
        return IDENTITY_FILE.read_text(encoding="utf-8")

    mission_chunks = _load_source(MISSION_DOC.parent)
    persona_chunks = _load_source(PERSONA_DOC.parent)
    chunks = mission_chunks + persona_chunks
    embedded = embedder.embed_chunks(chunks)
    _store_vectors(embedded)
    prompt = "\n\n".join(chunk["text"] for chunk in chunks)
    summary = glm.complete(prompt)
    IDENTITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDENTITY_FILE.write_text(summary, encoding="utf-8")
    update_entries = [
        {
            "source_path": chunk.get("source_path"),
            "embedding": chunk.get("embedding"),
        }
        for chunk in embedded
    ]
    update_insights(update_entries)
    return summary


__all__ = ["load_identity", "MISSION_DOC", "PERSONA_DOC", "IDENTITY_FILE"]
