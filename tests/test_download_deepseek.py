import importlib
import sys
import types

import pytest


@pytest.fixture
def dl_module(monkeypatch):
    dummy_dotenv = types.ModuleType("dotenv")
    dummy_dotenv.load_dotenv = lambda: None
    dummy_hub = types.ModuleType("huggingface_hub")
    dummy_hub.snapshot_download = lambda **kwargs: None
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)
    monkeypatch.setitem(sys.modules, "huggingface_hub", dummy_hub)
    return importlib.reload(importlib.import_module("download_model"))


def test_download_deepseek_success(dl_module, monkeypatch, capsys):
    calls = {}

    def fake_snapshot_download(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(dl_module, "snapshot_download", fake_snapshot_download)
    monkeypatch.setenv("HF_TOKEN", "test-token")

    dl_module.download_deepseek()

    out = capsys.readouterr().out
    assert "Model downloaded to" in out
    assert calls["repo_id"] == "deepseek-ai/DeepSeek-R1"
    assert calls["token"] == "test-token"
    assert calls["local_dir"].endswith("INANNA_AI/models/DeepSeek-R1")
    assert calls["local_dir_use_symlinks"] is False


def test_download_deepseek_missing_token(dl_module, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="HF_TOKEN environment variable not set"):
        dl_module.download_deepseek()


def test_download_deepseek_download_failure(dl_module, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "abc")

    def fake_snapshot_download(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(dl_module, "snapshot_download", fake_snapshot_download)
    with pytest.raises(SystemExit, match="Model download failed: boom"):
        dl_module.download_deepseek()
