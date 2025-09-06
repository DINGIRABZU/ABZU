"""FastAPI app exposing ignition, status and handover controls."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from razar import boot_orchestrator, ai_invoker, status_dashboard

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "web_operator" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


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


@app.get("/status")
async def status() -> dict:
    """Return component statuses from RAZAR."""
    components = status_dashboard._component_statuses()
    return {"components": components}


@app.post("/handover")
async def handover(payload: dict) -> StreamingResponse:
    """Delegate failure via ``ai_invoker.handover`` and stream logs."""
    component = payload.get("component", "")
    error = payload.get("error", "")
    logs = ai_invoker.handover(component, error)
    return StreamingResponse(_stream(logs), media_type="text/plain")
