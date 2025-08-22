import importlib
import sys

import pytest

from network_stubs import make_dotenv_stub, make_hub_stub


@pytest.fixture
def dl_module(monkeypatch):
    """Reload ``download_model`` with stubbed external dependencies."""
    hub = make_hub_stub()
    monkeypatch.setitem(sys.modules, "huggingface_hub", hub)
    monkeypatch.setitem(sys.modules, "dotenv", make_dotenv_stub())
    module = importlib.reload(importlib.import_module("download_model"))
    return module, hub


def test_download_deepseek_success(dl_module, monkeypatch, capsys):
    module, hub = dl_module
    monkeypatch.setenv("HF_TOKEN", "test-token")

    module.download_deepseek()

    out = capsys.readouterr().out
    assert "Model downloaded to" in out
    call = hub.calls[0]
    assert call["repo_id"] == "deepseek-ai/DeepSeek-R1"
    assert call["token"] == "test-token"
    assert call["local_dir"].endswith("INANNA_AI/models/DeepSeek-R1")
    assert call["local_dir_use_symlinks"] is False


def test_download_deepseek_missing_token(dl_module, monkeypatch):
    module, _ = dl_module
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="HF_TOKEN environment variable not set"):
        module.download_deepseek()


def test_download_deepseek_download_failure(dl_module, monkeypatch):
    module, hub = dl_module
    monkeypatch.setenv("HF_TOKEN", "abc")
    hub.should_fail = True
    with pytest.raises(SystemExit, match="Model download failed: boom"):
        module.download_deepseek()
