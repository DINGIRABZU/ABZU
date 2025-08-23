"""Tests for introspection api."""

from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

pytest.importorskip("omegaconf")

import introspection_api


def test_ast_endpoint_allows_repo_path():
    mod = introspection_api.ALLOWED_DIRS[0] / "mod.py"
    mod.write_text("x = 1\n", encoding="utf-8")
    try:
        client = TestClient(introspection_api.app)
        res = client.get("/ast", params={"module": str(mod)})
        assert res.status_code == 200
        data = res.json()
        assert "Module" in data["ast"]
        assert data["module"] == str(mod.resolve())
    finally:
        mod.unlink()


def test_ast_endpoint_rejects_escape(tmp_path):
    mod = tmp_path / "mod.py"
    mod.write_text("x = 1\n", encoding="utf-8")
    client = TestClient(introspection_api.app)
    res = client.get("/ast", params={"module": str(mod)})
    assert res.status_code == 403
