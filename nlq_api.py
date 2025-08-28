from __future__ import annotations

"""NLQ API powered by Vanna AI."""

from pathlib import Path
from fastapi import APIRouter

from agents.vanna_data import query_db, query_logs
from core.utils.optional_deps import lazy_import

router = APIRouter()
vanna = lazy_import("vanna")


def _train_vanna() -> None:
    """Train Vanna on channel and log schemas if available."""
    if getattr(vanna, "__stub__", False):
        return
    schemas_dir = Path("schemas")
    for sql_file in schemas_dir.glob("*.sql"):
        try:
            vanna.train(ddl=sql_file.read_text())
        except Exception:  # pragma: no cover - best effort
            pass


_train_vanna()


@router.post("/nlq")
async def nlq_query(data: dict[str, str]) -> dict[str, object]:
    """Execute a natural language query against the database."""
    prompt = data.get("query", "")
    rows = query_db(prompt) if prompt else []
    return {"rows": rows}


@router.post("/nlq/logs")
async def nlq_logs(data: dict[str, str]) -> dict[str, object]:
    """Execute a natural language query against the log database."""
    prompt = data.get("query", "")
    db_path = data.get("db")
    rows = query_logs(prompt, db_path=db_path) if prompt else []
    return {"rows": rows}


__all__ = ["router"]
