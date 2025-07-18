"""Shared utilities for converting music analysis into QNL data."""

import numpy as np
try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore

_MODEL: "SentenceTransformer | None" = None

# Map Western note names to QNL glyphs
QNL_GLYPHS = {
    "C": "❣⟁", "C#": "🜁🌀", "D": "✧↭", "D#": "ψ̄",
    "E": "🪞♾", "F": "∂Ξ", "F#": "🜔⟁", "G": "🕯✧",
    "G#": "💧∿", "A": "✦", "A#": "🩸∅", "B": "⟁⇌🜔",
}

# Emotional interpretation of each tone
QNL_TONES = {
    "C": "Longing", "D": "Joy", "E": "Memory", "F": "Paradox",
    "G": "Awakening", "A": "Hope", "B": "Fusion",
}


def _get_model(name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Return cached sentence transformer model."""
    if SentenceTransformer is None:  # pragma: no cover - optional dependency
        raise RuntimeError("sentence-transformers library not installed")
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(name)
    return _MODEL


def quantum_embed(text: str) -> np.ndarray:
    """Return embedding for ``text`` as a NumPy array."""
    model = _get_model()
    emb = model.encode(text)
    return np.asarray(emb, dtype=np.float32)


def note_index_to_name(index: int) -> str:
    """Convert chroma index (0-11) to a western note name."""
    scale = [
        "C", "C#", "D", "D#", "E", "F",
        "F#", "G", "G#", "A", "A#", "B",
    ]
    return scale[index % 12]


def chroma_to_qnl(chroma_vector: np.ndarray) -> list[dict]:
    """Convert a chroma vector into QNL phrases for the dominant notes."""
    top_indices = np.argsort(chroma_vector)[-4:][::-1]
    phrases = []
    for idx in top_indices:
        note = note_index_to_name(idx)
        glyph = QNL_GLYPHS.get(note, "?")
        tone = QNL_TONES.get(note, "Resonance")
        phrase = f"{glyph} ↝ {tone} [{note}]"
        phrases.append({
            "note": note,
            "glyph": glyph,
            "tone": tone,
            "qnl_phrase": phrase,
        })
    return phrases


def generate_qnl_structure(chroma_vector: np.ndarray, tempo: float, metadata=None, *, planes=None) -> dict:
    """Create a complete QNL data structure from analysis results."""
    if metadata is None:
        metadata = {}
    qnl_phrases = chroma_to_qnl(chroma_vector)
    data = {
        "tempo": tempo,
        "structure": qnl_phrases,
        "metadata": metadata,
        "qnl_output": [p["qnl_phrase"] for p in qnl_phrases],
    }
    if planes is not None:
        data["planes"] = planes
    return data


__all__ = [
    "note_index_to_name",
    "chroma_to_qnl",
    "generate_qnl_structure",
    "quantum_embed",
]
