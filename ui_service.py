"""Lightweight UI service exposing memory and status endpoints."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator

from memory.query_memory import query_memory

app = FastAPI(title="UI Service")
Instrumentator().instrument(app).expose(app)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Serve the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/boot", response_class=HTMLResponse)
async def boot(request: Request) -> HTMLResponse:
    """Serve the boot page styled like a classic arcade console."""
    return templates.TemplateResponse("boot.html", {"request": request})


@app.get("/status")
async def status() -> Dict[str, str]:
    """Return a simple status indicator."""
    return {"status": "ok"}


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    """Alias for Kubernetes health probes."""
    return {"status": "ok"}


@app.get("/memory/query")
async def memory_query(query: str) -> Dict[str, Any]:
    """Return aggregated memory search results."""
    return query_memory(query)


__all__ = ["app"]
