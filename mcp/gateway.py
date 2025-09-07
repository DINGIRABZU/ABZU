"""Model Context Protocol gateway.

This server bridges existing FastAPI routes with the Model Context Protocol
(MCP). It loads internal models from configuration and exposes handlers for
context registration and model invocation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import tomllib
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from invocation_engine import invoke

__version__ = "0.1.0"

server = FastMCP("abzu-mcp")
contexts: Dict[str, Dict[str, Any]] = {}
models: Dict[str, str] = {}
rate_limit: int = 0
auth_key: str | None = None


@server.tool()
async def register_context(
    id: str, data: Dict[str, Any] | None = None
) -> Dict[str, str]:
    """Register ``data`` for ``id`` and return confirmation."""
    contexts[id] = data or {}
    return {"status": "registered"}


@server.custom_route("/context/register", methods=["POST"])
async def register_context_route(request: Request) -> JSONResponse:
    payload = await request.json()
    result = await register_context(payload.get("id", ""), payload.get("data"))
    return JSONResponse(result)


@server.tool()
async def invoke_model(model: str, text: str) -> Dict[str, Any]:
    """Invoke ``model`` with ``text`` via the existing invocation engine."""
    if model not in models:
        raise ValueError("unknown model")
    result = invoke(text)
    return {"model": model, "result": result}


@server.custom_route("/model/invoke", methods=["POST"])
async def invoke_model_route(request: Request) -> JSONResponse:
    if auth_key and request.headers.get("x-api-key") != auth_key:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await request.json()
    result = await invoke_model(payload.get("model", ""), payload.get("text", ""))
    return JSONResponse(result)


def _load_config() -> None:
    """Populate models, rate limits, and auth key from ``config/mcp.toml``."""
    global rate_limit, auth_key
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "mcp.toml"
    with cfg_path.open("rb") as fh:
        cfg = tomllib.load(fh)
    models.update(cfg.get("models", {}))
    rate_limit = int(cfg.get("rate_limits", {}).get("requests_per_minute", 0))
    auth_key = cfg.get("auth", {}).get("key")


def main() -> None:
    """Start the MCP server after loading configuration."""
    _load_config()
    server.run()


if __name__ == "__main__":  # pragma: no cover - manual invocation only
    main()
