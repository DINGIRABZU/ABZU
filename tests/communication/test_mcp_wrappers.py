from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path

import httpx
import pytest
from tests.conftest import allow_test

allow_test(Path(__file__).resolve())
os.environ["ANYIO_BACKEND"] = "asyncio"


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio("asyncio")
async def test_mcp_handshake_and_logging(monkeypatch):
    prim_calls: list[dict[str, int]] = []
    prim_mod = types.ModuleType("connectors.primordials_api")
    prim_mod.send_metrics = lambda m: prim_calls.append(m) or True  # type: ignore[assignment]
    sys.modules["connectors.primordials_api"] = prim_mod

    narr_calls: list[str] = []
    narr_mod = types.ModuleType("narrative_api")

    class Story:
        def __init__(self, text: str) -> None:
            self.text = text

    narr_mod.Story = Story

    def _log_story(story: Story) -> dict[str, str]:
        narr_calls.append(story.text)
        return {"status": "ok"}

    narr_mod.log_story = _log_story  # type: ignore[assignment]
    sys.modules["narrative_api"] = narr_mod

    spec = importlib.util.spec_from_file_location(
        "gateway", Path(__file__).resolve().parents[2] / "mcp" / "gateway.py"
    )
    gateway = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(gateway)
    app = gateway.server.streamable_http_app()

    transport = httpx.ASGITransport(app=app)

    class LocalClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("transport", transport)
            kwargs.setdefault("base_url", "http://mcp")
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", LocalClient)
    monkeypatch.setenv("ABZU_USE_MCP", "1")
    monkeypatch.setenv("MCP_GATEWAY_URL", "http://mcp")

    prim_spec = importlib.util.spec_from_file_location(
        "primordials_mcp",
        Path(__file__).resolve().parents[2] / "connectors" / "primordials_mcp.py",
    )
    prim = importlib.util.module_from_spec(prim_spec)
    assert prim_spec.loader is not None
    prim_spec.loader.exec_module(prim)

    narr_spec = importlib.util.spec_from_file_location(
        "narrative_mcp",
        Path(__file__).resolve().parents[2] / "connectors" / "narrative_mcp.py",
    )
    narr = importlib.util.module_from_spec(narr_spec)
    assert narr_spec.loader is not None
    narr_spec.loader.exec_module(narr)

    assert await prim.handshake("prim") == {"status": "registered"}
    assert await prim.send_metrics({"foo": 1}) == {"status": "sent"}
    assert prim_calls == [{"foo": 1}]

    assert await narr.handshake("narr") == {"status": "registered"}
    assert await narr.log_story("hello") == {"status": "logged"}
    assert narr_calls == ["hello"]
