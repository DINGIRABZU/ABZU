"""Lightweight UI service exposing memory and status endpoints."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from memory.query_memory import query_memory

app = FastAPI(title="UI Service")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Serve the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/status")
async def status() -> Dict[str, str]:
    """Return a simple status indicator."""
    return {"status": "ok"}


@app.get("/memory/query")
async def memory_query(query: str) -> Dict[str, Any]:
    """Return aggregated memory search results."""
    return query_memory(query)


__all__ = ["app"]
