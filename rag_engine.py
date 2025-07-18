from __future__ import annotations

"""Retrieval helper for vector memory documents."""

from typing import Any, Dict, List, Optional
import argparse
import importlib.util

from vector_memory import search as vm_search
_HAYSTACK_AVAILABLE = importlib.util.find_spec("haystack") is not None
_LLAMA_AVAILABLE = importlib.util.find_spec("llama_index") is not None or importlib.util.find_spec("llamaindex") is not None


def _make_item(text: str, meta: Dict[str, Any], score: float) -> Any:
    if _HAYSTACK_AVAILABLE:
        try:
            from haystack import Document
        except Exception:  # pragma: no cover - optional dep missing at runtime
            pass
        else:
            doc = Document(content=text, meta=meta)
            doc.score = score  # type: ignore[attr-defined]
            return doc
    if _LLAMA_AVAILABLE:
        try:
            from llama_index.core.schema import TextNode, NodeWithScore
        except Exception:  # pragma: no cover - optional dep missing at runtime
            pass
        else:
            node = TextNode(text=text, metadata=meta)
            return NodeWithScore(node=node, score=score)
    return {"snippet": text, "metadata": meta, "score": score}


def _get_score(item: Any) -> float:
    if isinstance(item, dict):
        return float(item.get("score", 0.0))
    return float(getattr(item, "score", 0.0))


def query(text: str, filters: Optional[Dict[str, Any]] = None, *, top_n: int = 5) -> List[Any]:
    """Return ranked snippets for ``text``."""
    res = vm_search(text, filter=filters, k=top_n)
    items = [_make_item(r.get("text", ""), r, r.get("score", 0.0)) for r in res]
    items.sort(key=_get_score, reverse=True)
    return items


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag_engine")
    parser.add_argument("--query", required=True, help="Text to search")
    parser.add_argument(
        "--filter",
        action="append",
        help="Metadata filter as key=value (can repeat)",
    )
    args = parser.parse_args(argv)
    filt: Dict[str, str] | None = None
    if args.filter:
        filt = {}
        for kv in args.filter:
            if "=" in kv:
                k, v = kv.split("=", 1)
                filt[k] = v
    results = query(args.query, filters=filt)
    for item in results:
        score = _get_score(item)
        text = ""
        if isinstance(item, dict):
            text = item.get("snippet", "")
        else:
            text = getattr(item, "content", None)
            if text is None:
                node = getattr(item, "node", None)
                text = getattr(node, "text", "")
        print(f"{score:.2f}: {text}")
    return 0


__all__ = ["query", "main"]


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
