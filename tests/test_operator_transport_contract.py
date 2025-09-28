"""Dual-transport contract tests for operator_api."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import operator_api
from operator_api_grpc import OperatorApiGrpcService


def _rest_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()
    app.include_router(operator_api.router)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs" / "operators").mkdir(parents=True)
    client = TestClient(app)
    return client


class _DummyContext:
    """Minimal context stub capturing metadata for gRPC handler tests."""

    def __init__(self) -> None:
        self.trailing_metadata: tuple[tuple[str, str], ...] | None = None

    async def abort(self, status_code, details):
        raise RuntimeError(f"abort: {status_code}: {details}")

    def set_trailing_metadata(self, metadata):
        if metadata is None:
            self.trailing_metadata = None
        else:
            self.trailing_metadata = tuple(metadata)

    # The remaining gRPC context hooks are no-ops for these tests
    def set_code(self, _code):
        return None

    def set_details(self, _details):
        return None

    def send_initial_metadata(self, _metadata):
        return None

    def set_compression(self, _compression):
        return None

    def disable_next_message_compression(self):
        return None

    async def write(self, _response):
        return None

    async def read(self):
        return None


def test_grpc_rest_command_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _run() -> None:
        client = _rest_client(tmp_path, monkeypatch)
        service = OperatorApiGrpcService()
        try:
            rest_response = client.post(
                "/operator/command",
                json={"operator": "crown", "agent": "razar", "command": "status"},
            )
            assert rest_response.status_code == 200
            rest_body = rest_response.json()
            context = _DummyContext()
            grpc_body = await service._dispatch_command(
                {"operator": "crown", "agent": "razar", "command": "status"},
                context,
            )
        finally:
            client.close()
        assert rest_body["result"] == grpc_body["result"]
        assert rest_body["result"] == {"ack": "status"}
        assert rest_body["command_id"]
        assert grpc_body["command_id"]

    asyncio.run(_run())


def test_grpc_fallback_emits_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _run() -> None:
        client = _rest_client(tmp_path, monkeypatch)
        calls: dict[str, Any] = {"count": 0}
        original_dispatch = operator_api._dispatcher.dispatch

        def _patched_dispatch(*args: Any, **kwargs: Any) -> Any:
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("grpc failure")
            return original_dispatch(*args, **kwargs)

        monkeypatch.setattr(operator_api._dispatcher, "dispatch", _patched_dispatch)
        service = OperatorApiGrpcService(enable_rest_fallback=True)
        try:
            context = _DummyContext()
            body = await service._dispatch_command(
                {"operator": "crown", "agent": "razar", "command": "status"},
                context,
            )
        finally:
            client.close()
        assert body["result"] == {"ack": "status"}
        assert context.trailing_metadata == (("abzu-fallback", "rest"),)
        assert calls["count"] == 2

    asyncio.run(_run())
