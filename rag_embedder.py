from __future__ import annotations

"""Embed RAG text chunks with optional sentiment tags."""

from pathlib import Path
from typing import Iterable, List, Dict, Any
import argparse
import json
import os

import numpy as np

try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore

from INANNA_AI.utils import sentiment_score

_MODEL: Any | None = None


def _get_model() -> Any:
    """Return embedding model instance."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    model_path = os.getenv("EMBED_MODEL_PATH", "all-MiniLM-L6-v2")
    if SentenceTransformer is not None:
        _MODEL = SentenceTransformer(model_path)
    else:  # pragma: no cover - fallback for tests
        class DummyModel:
            def encode(self, texts: Iterable[str], **_: Any) -> List[List[float]]:
                if isinstance(texts, str):
                    texts = [texts]
                return [[float(len(t))] for t in texts]

        _MODEL = DummyModel()
    return _MODEL


def embed_chunks(chunks: Iterable[dict]) -> list[dict]:
    """Return ``chunks`` with embedding and sentiment fields added."""
    items = list(chunks)
    model = _get_model()
    texts = [c.get("text", "") for c in items]
    embeddings = model.encode(texts)
    out: list[dict] = []
    for chunk, emb in zip(items, embeddings):
        sent = sentiment_score(chunk.get("text", ""))
        tag = "positive" if sent > 0 else "negative" if sent < 0 else "neutral"
        record = {
            "text": chunk.get("text", ""),
            "source_path": chunk.get("source_path", ""),
            "embedding": list(map(float, np.asarray(emb).flatten().tolist())),
            "sentiment": tag,
        }
        if "archetype" in chunk:
            record["archetype"] = chunk["archetype"]
        out.append(record)
    return out


def _load_chunks(path: Path) -> list[dict]:
    """Load JSON or JSONL chunks from ``path``."""
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [dict(d) for d in data]
    except Exception:
        pass
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except Exception:
            continue
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag_embedder")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON/JSONL")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSONL")
    args = parser.parse_args(argv)
    chunks = _load_chunks(Path(args.in_path))
    results = embed_chunks(chunks)
    out_file = Path(args.out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as fh:
        for rec in results:
            fh.write(json.dumps(rec, ensure_ascii=False))
            fh.write("\n")
    return 0


__all__ = ["embed_chunks", "main"]

if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
