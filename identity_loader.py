"""Load and persist system identity using RAG and insight passes."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict

from INANNA_AI.glm_integration import GLMIntegration
from rag import parser, embedder
import vector_memory
from insight_compiler import update_insights

__version__ = "0.1.0"

IDENTITY_FILE = Path("data/identity.json")
MISSION_DOC = Path("docs/project_mission_vision.md")
PERSONA_DOC = Path("docs/persona_api_guide.md")


def _load_chunks(paths: Iterable[Path]) -> List[Dict[str, str]]:
    """Return parsed chunks for the given document ``paths``."""
    chunks: List[Dict[str, str]] = []
    for doc in paths:
        for item in parser.load_inputs(doc.parent):
            if item.get("source_path") == str(doc):
                chunks.append(item)
    return chunks


def load_identity(integration: GLMIntegration) -> str:
    """Digest mission, vision, and persona docs and persist identity.

    Uses the RAG parser and embedder to index the documents into vector
    memory, then asks the provided ``integration`` for a summary which is
    stored at :data:`IDENTITY_FILE` for reuse.
    """
    if IDENTITY_FILE.exists():
        return IDENTITY_FILE.read_text(encoding="utf-8")

    docs = [MISSION_DOC, PERSONA_DOC]
    chunks = _load_chunks(docs)
    embedded = embedder.embed_chunks(chunks)
    texts = [c.get("text", "") for c in embedded]
    metas = [{"source_path": c.get("source_path", "")} for c in embedded]
    if texts:
        vector_memory.add_vectors(texts, metas)
    combined = "\n".join(texts)
    summary = integration.complete(
        "Summarize the mission, vision, and persona: \n" + combined
    )
    update_insights(
        [
            {
                "intent": "identity_load",
                "tone": "neutral",
                "success": True,
                "result": {"identity": summary},
            }
        ]
    )
    IDENTITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDENTITY_FILE.write_text(summary, encoding="utf-8")
    return summary


__all__ = ["load_identity", "IDENTITY_FILE", "MISSION_DOC", "PERSONA_DOC"]
