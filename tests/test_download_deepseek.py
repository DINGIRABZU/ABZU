"""Tests for download deepseek."""

from __future__ import annotations

import importlib
import logging
import sys
import types

import pytest

download_model = importlib.import_module("download_model")


def _patch(monkeypatch):
    dummy_dotenv = types.ModuleType("dotenv")
    dummy_dotenv.load_dotenv = lambda: None
    dummy_hub = types.ModuleType("huggingface_hub")
    dummy_utils = types.ModuleType("huggingface_hub.utils")
    dummy_utils.HfHubHTTPError = RuntimeError
    dummy_hub.snapshot_download = lambda **kwargs: None
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)
    monkeypatch.setitem(sys.modules, "huggingface_hub", dummy_hub)
    monkeypatch.setitem(sys.modules, "huggingface_hub.utils", dummy_utils)
    return dummy_hub, dummy_utils


def test_download_deepseek_success(monkeypatch, caplog):
    hub, _ = _patch(monkeypatch)
    calls = {}

    def fake_snapshot_download(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(hub, "snapshot_download", fake_snapshot_download)
    monkeypatch.setenv("HF_TOKEN", "test-token")

    with caplog.at_level(logging.INFO):
        download_model.download_deepseek()

    assert "Model downloaded to" in caplog.text
    assert calls["repo_id"] == "deepseek-ai/DeepSeek-R1"
    assert calls["token"] == "test-token"
    assert calls["local_dir"].endswith("INANNA_AI/models/DeepSeek-R1")
    assert calls["local_dir_use_symlinks"] is False


def test_download_deepseek_missing_token(monkeypatch, caplog):
    _patch(monkeypatch)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit, match="HF_TOKEN environment variable not set"):
            download_model.download_deepseek()
    assert "HF_TOKEN environment variable not set" in caplog.text


def test_download_deepseek_download_failure(monkeypatch, caplog):
    hub, utils = _patch(monkeypatch)
    monkeypatch.setenv("HF_TOKEN", "abc")

    def fake_snapshot_download(**kwargs):
        raise utils.HfHubHTTPError("boom")

    monkeypatch.setattr(hub, "snapshot_download", fake_snapshot_download)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit, match="Model download failed: boom"):
            download_model.download_deepseek()
    assert "Model download failed: boom" in caplog.text
