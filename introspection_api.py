"""FastAPI service exposing an endpoint to return the AST of a module."""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Allowed directories for module inspection; defaults to repository root.
ALLOWED_DIRS = [Path(__file__).resolve().parent]


class ASTQuery(BaseModel):
    """Query parameters for ``/ast``."""

    module: str


@app.get("/ast")
def get_ast(params: ASTQuery = Depends()) -> dict:
    """Return the abstract syntax tree for ``params.module``."""
    path = Path(params.module)
    try:
        resolved = path.expanduser().resolve(strict=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="module not found")

    if not any(resolved.is_relative_to(base) for base in ALLOWED_DIRS):
        raise HTTPException(status_code=403, detail="module not allowed")

    try:
        tree = ast.parse(resolved.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - parse failures
        raise HTTPException(status_code=400, detail=str(exc))
    return {"module": str(resolved), "ast": ast.dump(tree)}


__all__ = ["app"]
