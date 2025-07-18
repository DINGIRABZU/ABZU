from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from types import ModuleType

import httpx

try:  # fall back to simple stubs if FastAPI is unavailable
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover - environment lacks FastAPI
    import json

    class FastAPI:
        def __init__(self) -> None:
            self.routes: dict[tuple[str, str], any] = {}

        def get(self, path: str):
            def decorator(func: any) -> any:
                self.routes[("GET", path)] = func
                return func

            return decorator

        def post(self, path: str):
            def decorator(func: any) -> any:
                self.routes[("POST", path)] = func
                return func

            return decorator

        async def __call__(self, scope: dict, receive: any, send: any) -> None:
            method = scope["method"]
            path = scope["path"]
            handler = self.routes.get((method, path))
            status = 200
            result: dict[str, str] | None = None
            if handler is None:
                status = 404
                result = {}
            else:
                if method == "POST":
                    body = b""
                    more = True
                    while more:
                        event = await receive()
                        body += event.get("body", b"")
                        more = event.get("more_body", False)
                    data = json.loads(body.decode() or "{}")
                    res = handler(data)
                else:
                    res = handler()
                if asyncio.iscoroutine(res):
                    res = await res
                result = res
            content = json.dumps(result or {}).encode()
            headers = [(b"content-type", b"application/json")]
            await send({"type": "http.response.start", "status": status, "headers": headers})
            await send({"type": "http.response.body", "body": content})

    class TestClient:
        __test__ = False
        def __init__(self, app: any) -> None:
            self.app = app

        def __enter__(self) -> "TestClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            pass


try:
    from aiortc import RTCSessionDescription
except Exception:  # pragma: no cover - environment lacks aiortc
    class RTCSessionDescription:
        def __init__(self, sdp: str, type: str) -> None:
            self.sdp = sdp
            self.type = type

    aiortc_stub = ModuleType("aiortc")
    aiortc_stub.RTCSessionDescription = RTCSessionDescription
    aiortc_stub.RTCPeerConnection = object
    sys.modules.setdefault("aiortc", aiortc_stub)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_vast_check_success(monkeypatch, capsys):
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.post("/offer")
    async def offer(data: dict) -> dict[str, str]:
        return {"sdp": "ans", "type": "answer"}

    mod = importlib.import_module("scripts.vast_check")

    class DummyPC:
        def __init__(self) -> None:
            self.localDescription = RTCSessionDescription(sdp="off", type="offer")

        def addTransceiver(self, kind: str) -> None:
            pass

        async def createOffer(self) -> RTCSessionDescription:
            return RTCSessionDescription(sdp="off", type="offer")

        async def setLocalDescription(self, desc: RTCSessionDescription) -> None:
            self.localDescription = desc

        async def setRemoteDescription(self, desc: RTCSessionDescription) -> None:
            self.remote = desc

        async def close(self) -> None:
            pass

    with TestClient(app) as test_client:
        transport = httpx.ASGITransport(app=test_client.app)

        orig_client = httpx.AsyncClient

        class PatchedAsyncClient(orig_client):
            def __init__(self, *args, **kwargs):
                kwargs.setdefault("transport", transport)
                super().__init__(*args, **kwargs)

        monkeypatch.setattr(mod.httpx, "AsyncClient", PatchedAsyncClient)
        monkeypatch.setattr(mod, "RTCPeerConnection", DummyPC)

        argv = sys.argv.copy()
        sys.argv = ["vast_check.py", "http://testserver"]
        try:
            asyncio.run(mod.main())
        finally:
            sys.argv = argv

    out = capsys.readouterr().out
    assert "Server is ready" in out
