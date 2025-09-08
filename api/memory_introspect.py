"""FastAPI application exposing memory introspection endpoints."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.memory_introspect import router, __version__

app = FastAPI()
Instrumentator().instrument(app).expose(app)
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok"}


__all__ = ["app", "__version__"]
