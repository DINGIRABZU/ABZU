"""FastAPI service exposing an endpoint to return the AST of a module."""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/ast")
def get_ast(module: str) -> dict:
    """Return the abstract syntax tree for ``module``.

    Parameters
    ----------
    module:
        File system path to a Python module.
    """
    path = Path(module)
    if not path.exists():
        raise HTTPException(status_code=404, detail="module not found")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - parse failures
        raise HTTPException(status_code=400, detail=str(exc))
    return {"module": str(path), "ast": ast.dump(tree)}


__all__ = ["app"]
