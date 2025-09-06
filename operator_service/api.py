"""FastAPI app exposing ignition, query, and status controls."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator

from memory import query_memory
from razar import boot_orchestrator, status_dashboard

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1] / "web_operator"
TEMPLATE_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")
Instrumentator().instrument(app).expose(app)


def _stream(result: Iterable[str]) -> Iterator[str]:
    """Yield items from ``result`` as strings."""
    for item in result:
        yield item if item.endswith("\n") else f"{item}\n"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve arcade operator interface."""
    return templates.TemplateResponse("arcade.html", {"request": request})


@app.post("/start_ignition")
async def start_ignition() -> StreamingResponse:
    """Kick off ignition via ``boot_orchestrator.start`` and stream logs."""
    logs = boot_orchestrator.start()  # type: ignore[attr-defined]
    return StreamingResponse(_stream(logs), media_type="text/plain")


@app.post("/query")
async def query(payload: dict) -> dict:
    """Return aggregated memory search results via ``query_memory``."""
    text = payload.get("query", "")
    return query_memory(text)


@app.get("/memory/query")
async def memory_query(prompt: str) -> dict:
    """Return aggregated memory search results via ``query_memory``."""
    return query_memory(prompt)


@app.get("/status")
async def status() -> dict:
    """Return component statuses from RAZAR."""
    components = status_dashboard._component_statuses()
    return {"components": components}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok"}
