"""Tests for the DeepSeek model downloader."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

download_model = importlib.import_module("download_model")


def test_main_invokes_snapshot_download(monkeypatch):
    dummy_dotenv = ModuleType("dotenv")
    dummy_dotenv.load_dotenv = lambda: None
    dummy_hf = ModuleType("huggingface_hub")
    dummy_utils = ModuleType("huggingface_hub.utils")
    calls = {}

    def dummy_snapshot_download(**kwargs):
        calls.update(kwargs)

    dummy_hf.snapshot_download = dummy_snapshot_download
    dummy_utils.HfHubHTTPError = RuntimeError
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)
    monkeypatch.setitem(sys.modules, "huggingface_hub", dummy_hf)
    monkeypatch.setitem(sys.modules, "huggingface_hub.utils", dummy_utils)
    monkeypatch.setenv("HF_TOKEN", "test-token")

    download_model.main()

    expected_dir = str(Path("INANNA_AI") / "models" / "DeepSeek-R1")
    assert calls == {
        "repo_id": "deepseek-ai/DeepSeek-R1",
        "token": "test-token",
        "local_dir": expected_dir,
        "local_dir_use_symlinks": False,
    }


def test_main_exits_without_token(monkeypatch):
    dummy_dotenv = ModuleType("dotenv")
    dummy_dotenv.load_dotenv = lambda: None
    dummy_hf = ModuleType("huggingface_hub")
    dummy_utils = ModuleType("huggingface_hub.utils")
    dummy_utils.HfHubHTTPError = RuntimeError
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)
    monkeypatch.setitem(sys.modules, "huggingface_hub", dummy_hf)
    monkeypatch.setitem(sys.modules, "huggingface_hub.utils", dummy_utils)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        download_model.main()
