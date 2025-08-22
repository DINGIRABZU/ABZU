from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
import hashlib

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _prepare(monkeypatch):
    dummy_hf = ModuleType("huggingface_hub")
    dummy_hf.snapshot_download = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "huggingface_hub", dummy_hf)
    dummy_dotenv = ModuleType("dotenv")
    dummy_dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)
    dummy_tf = ModuleType("transformers")

    class DummyModel:
        called = {}

        @classmethod
        def from_pretrained(cls, path, device_map=None, load_in_8bit=False):
            cls.called["args"] = (path, load_in_8bit)
            return cls()

        def save_pretrained(self, path):
            DummyModel.called["save"] = path

    dummy_tf.AutoModelForCausalLM = DummyModel
    monkeypatch.setitem(sys.modules, "transformers", dummy_tf)


def test_main_deepseek_calls_download(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")

    called = {}
    monkeypatch.setattr(
        module, "download_deepseek", lambda: called.setdefault("deepseek", True)
    )

    argv = sys.argv.copy()
    sys.argv = ["download_models.py", "deepseek"]
    try:
        module.main()
    finally:
        sys.argv = argv

    assert called == {"deepseek": True}


def test_main_gemma2_invokes_ollama(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")

    runs = []

    def dummy_run(cmd, *args, **kwargs):
        runs.append((cmd, kwargs))

    monkeypatch.setattr(module.subprocess, "run", dummy_run)
    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/ollama")

    argv = sys.argv.copy()
    sys.argv = ["download_models.py", "gemma2"]
    try:
        module.main()
    finally:
        sys.argv = argv

    assert runs
    cmd, kwargs = runs[0]
    assert cmd == ["ollama", "pull", "gemma2"]
    assert kwargs["check"] is True
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert "env" in kwargs
    assert kwargs["env"]["OLLAMA_MODELS"].endswith("INANNA_AI/models")


def test_ollama_install_success(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")

    script = b"echo hi"
    digest = hashlib.sha256(script).hexdigest()

    class DummyResp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return script

    monkeypatch.setattr(module, "OLLAMA_INSTALL_SHA256", digest)
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda url: DummyResp())
    monkeypatch.setattr(module.shutil, "which", lambda _: None)

    runs = []

    def dummy_run(cmd, *args, **kwargs):
        runs.append((cmd, kwargs))

    monkeypatch.setattr(module.subprocess, "run", dummy_run)

    module.download_gemma2()

    assert len(runs) == 2
    install_cmd, install_kwargs = runs[0]
    pull_cmd, _ = runs[1]
    assert install_cmd[0] == "sh"
    assert install_kwargs["check"] is True
    assert pull_cmd == ["ollama", "pull", "gemma2"]


def test_ollama_install_network_failure(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")
    monkeypatch.setattr(module.shutil, "which", lambda _: None)

    def failing(url):
        raise OSError("no network")

    monkeypatch.setattr(module.urllib.request, "urlopen", failing)
    monkeypatch.setattr(
        module.subprocess, "run", lambda *a, **kw: pytest.fail("should not run")
    )

    with pytest.raises(RuntimeError):
        module.download_gemma2()


def test_ollama_install_hash_mismatch(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")

    script = b"bad"

    class DummyResp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return script

    monkeypatch.setattr(module, "OLLAMA_INSTALL_SHA256", "0" * 64)
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda url: DummyResp())
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    monkeypatch.setattr(
        module.subprocess, "run", lambda *a, **kw: pytest.fail("should not run")
    )

    with pytest.raises(RuntimeError, match="hash mismatch"):
        module.download_gemma2()


def test_glm41v_download_and_quant(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")
    monkeypatch.setenv("HF_TOKEN", "x")
    module.download_glm41v_9b(int8=True)
    called = sys.modules["transformers"].AutoModelForCausalLM.called
    assert called["args"][1] is True
    assert called["save"].endswith("GLM-4.1V-9B")


def test_cli_mistral_invokes_function(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")

    called = {}
    monkeypatch.setattr(
        module,
        "download_mistral_8x22b",
        lambda int8=False: called.setdefault("ok", int8),
    )

    argv = sys.argv.copy()
    sys.argv = ["download_models.py", "mistral_8x22b", "--int8"]
    try:
        module.main()
    finally:
        sys.argv = argv

    assert called == {"ok": True}


def test_cli_kimi_k2_invokes_function(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")

    called = {}
    monkeypatch.setattr(
        module, "download_kimi_k2", lambda int8=False: called.setdefault("ok", int8)
    )

    argv = sys.argv.copy()
    sys.argv = ["download_models.py", "kimi_k2"]
    try:
        module.main()
    finally:
        sys.argv = argv

    assert called == {"ok": False}


def test_get_hf_token_requires_env(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        module._get_hf_token()


def test_get_hf_token_returns_value(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")
    monkeypatch.setenv("HF_TOKEN", "secret")
    assert module._get_hf_token() == "secret"


def test_deepseek_v3_download_and_quant(monkeypatch):
    _prepare(monkeypatch)
    module = importlib.import_module("download_models")
    monkeypatch.setenv("HF_TOKEN", "x")
    called = {}
    monkeypatch.setattr(
        module,
        "snapshot_download",
        lambda **kw: called.setdefault("snap", kw),
    )
    monkeypatch.setattr(
        module,
        "_quantize_to_int8",
        lambda path: called.setdefault("quant", str(path)),
    )
    module.download_deepseek_v3(int8=True)
    assert called["snap"]["repo_id"] == "deepseek-ai/DeepSeek-V3"
    assert called["quant"].endswith("DeepSeek-V3")
