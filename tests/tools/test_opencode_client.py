"""Tests for ``tools.opencode_client``."""

from __future__ import annotations

import subprocess
import types

import pytest

from tools import opencode_client


def test_complete_via_cli(monkeypatch):
    """Should invoke local CLI when no backend or endpoint configured."""

    monkeypatch.setattr(opencode_client, "_ENDPOINT", "")
    monkeypatch.setattr(opencode_client, "_BACKEND", "")

    called = {}

    def fake_run(cmd, input=None, stdout=None, stderr=None, check=None, timeout=None):
        called["cmd"] = cmd
        return types.SimpleNamespace(stdout=b"diff", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = opencode_client.complete("code")

    assert called["cmd"] == ["opencode", "--diff"]
    assert result == "diff"


def test_complete_cli_failure(monkeypatch):
    """CLI failures should raise ``RuntimeError``."""

    monkeypatch.setattr(opencode_client, "_ENDPOINT", "")
    monkeypatch.setattr(opencode_client, "_BACKEND", "")

    def boom(*a, **k):
        raise subprocess.CalledProcessError(1, "opencode")

    monkeypatch.setattr(subprocess, "run", boom)

    with pytest.raises(RuntimeError):
        opencode_client.complete("bad")


def test_complete_http_endpoint(monkeypatch):
    """When an endpoint is configured, ``requests`` should be used."""

    monkeypatch.setattr(opencode_client, "_ENDPOINT", "http://api")
    monkeypatch.setattr(opencode_client, "_BACKEND", "")

    class DummyResponse:
        text = "raw"

        def raise_for_status(self):
            pass

        def json(self):
            return {"diff": "delta"}

    def fake_post(url, json, timeout):
        assert url == "http://api"
        assert json == {"prompt": "ping"}
        return DummyResponse()

    dummy_requests = types.SimpleNamespace(post=fake_post)
    monkeypatch.setattr(opencode_client, "requests", dummy_requests)

    result = opencode_client.complete("ping")

    assert result == "delta"


def test_complete_http_failure(monkeypatch):
    """HTTP errors should surface as ``RuntimeError``."""

    monkeypatch.setattr(opencode_client, "_ENDPOINT", "http://api")
    monkeypatch.setattr(opencode_client, "_BACKEND", "")

    def fake_post(*a, **k):
        raise ValueError("boom")

    dummy_requests = types.SimpleNamespace(post=fake_post)
    monkeypatch.setattr(opencode_client, "requests", dummy_requests)

    with pytest.raises(RuntimeError):
        opencode_client.complete("ping")


def test_complete_kimi_backend(monkeypatch):
    """Kimi backend should delegate to Kimi-K2 client."""

    monkeypatch.setattr(opencode_client, "_BACKEND", "kimi")
    monkeypatch.setattr(opencode_client, "_ENDPOINT", "")

    called = {}

    def fake_complete(prompt):
        called["prompt"] = prompt
        return "kimi"  # pragma: no cover - simulated

    monkeypatch.setattr(opencode_client.kimi_k2_client, "complete", fake_complete)

    result = opencode_client.complete("msg")

    assert called["prompt"] == "msg"
    assert result == "kimi"


def test_complete_kimi_failure(monkeypatch):
    """Failures from Kimi backend should raise ``RuntimeError``."""

    monkeypatch.setattr(opencode_client, "_BACKEND", "kimi")
    monkeypatch.setattr(opencode_client, "_ENDPOINT", "")

    def boom(prompt):
        raise RuntimeError("nope")

    monkeypatch.setattr(opencode_client.kimi_k2_client, "complete", boom)

    with pytest.raises(RuntimeError):
        opencode_client.complete("msg")
