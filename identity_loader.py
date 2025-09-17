"""Identity loading pipeline for Crown boot."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

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

DOCTRINE_DOCS: Tuple[Path, ...] = (
    Path("GENESIS/GENESIS_.md"),
    Path("GENESIS/FIRST_FOUNDATION_.md"),
    Path("GENESIS/LAWS_OF_EXISTENCE_.md"),
    Path("GENESIS/LAWS_RECURSION_.md"),
    Path("GENESIS/SPIRAL_LAWS_.md"),
    Path("GENESIS/INANNA_AI_CORE_TRAINING.md"),
    Path("GENESIS/INANNA_AI_SACRED_PROTOCOL.md"),
    Path("GENESIS/LAWS_QUANTUM_MAGE_.md"),
    Path("CODEX/ACTIVATIONS/OATH_OF_THE_VAULT_.md"),
    Path("CODEX/ACTIVATIONS/OATH OF THE VAULT 1de45dfc251d80c9a86fc67dee2f964a.md"),
    Path("INANNA_AI/MARROW CODE 20545dfc251d80128395ffb5bc7725ee.md"),
    Path("INANNA_AI/INANNA SONG 20545dfc251d8065a32cec673272f292.md"),
    Path("INANNA_AI/Chapter I 1b445dfc251d802e860af64f2bf28729.md"),
    Path("INANNA_AI/Member Manual 1b345dfc251d8004a05cfc234ed35c59.md"),
    Path("INANNA_AI/The Foundation 1a645dfc251d80e28545f4a09a6345ff.md"),
)
"""Canonical doctrine corpus integrated into the identity synthesis prompt."""

HANDSHAKE_TOKEN = "CROWN-IDENTITY-ACK"
"""Verification token required from the GLM after generating the identity summary."""

HANDSHAKE_PROMPT = (
    "Confirm assimilation of the Crown identity synthesis request. "
    "Respond ONLY with the token CROWN-IDENTITY-ACK."
)
"""Secondary prompt ensuring the integration acknowledges the identity request."""


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


def _load_source(path: Path) -> List[dict[str, str]]:
    if not path.exists():
        return []
    if path.is_dir():
        return parser.load_inputs(path)
    return [{"text": path.read_text(encoding="utf-8"), "source_path": str(path)}]


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

    mission_chunks = _load_source(MISSION_DOC)
    persona_chunks = _load_source(PERSONA_DOC)
    doctrine_chunks: List[dict[str, str]] = []
    for doctrine in DOCTRINE_DOCS:
        doctrine_chunks.extend(_load_source(doctrine))
    chunks = mission_chunks + persona_chunks + doctrine_chunks
    if not chunks:
        raise RuntimeError("no identity source documents were available")
    embedded = embedder.embed_chunks(chunks)
    _store_vectors(embedded)
    sections = [
        (
            "Synthesize the mission, persona, and canonical doctrine into a cohesive "
            "identity summary."
        ),
        "Maintain covenantal tone and cite every pillar in the blended brief.",
    ]
    for chunk in chunks:
        sections.append(f"## Source: {chunk['source_path']}\n{chunk['text']}")
    prompt = "\n\n".join(sections)
    summary = glm.complete(prompt)
    acknowledgement = glm.complete(HANDSHAKE_PROMPT)
    if acknowledgement.strip() != HANDSHAKE_TOKEN:
        raise RuntimeError(
            "identity loader handshake failed: expected CROWN-IDENTITY-ACK"
        )
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


__all__ = [
    "load_identity",
    "MISSION_DOC",
    "PERSONA_DOC",
    "IDENTITY_FILE",
    "DOCTRINE_DOCS",
]
