"""Minimal helper answering operator questions from the document registry.

This module exposes a small FastAPI router that searches the doctrine
corpus collected by :class:`agents.nazarick.document_registry.DocumentRegistry`.
It is intended for lightweight operator interactions via a chat pane.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Response
from typing import Dict
from prometheus_client import (
    CollectorRegistry,
    Counter,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

from agents.nazarick.document_registry import DocumentRegistry

router = APIRouter()

registry = CollectorRegistry()
QUERY_COUNTER = Counter(
    "sidekick_queries_total",
    "Total number of questions answered",
    registry=registry,
)

_registry = DocumentRegistry()
_corpus = {path: text.lower() for path, text in _registry.get_corpus().items()}


def _search(question: str) -> str:
    """Return a snippet from the first document containing ``question``."""
    q = question.lower()
    for path, text in _corpus.items():
        if q in text:
            idx = text.index(q)
            snippet = text[idx : idx + 200]
            return f"{path}: {snippet.strip()}"
    return "No relevant document found."


@router.post("/sidekick")
async def sidekick(payload: dict = Body(...)) -> dict[str, str]:
    """Answer operator questions using the document registry."""
    question = payload.get("question", "")
    QUERY_COUNTER.inc()
    return {"answer": _search(question)}


@router.get("/healthz")
def healthz() -> Dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics."""
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
