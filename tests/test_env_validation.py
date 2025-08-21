import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import env_validation


def test_check_required_pass(monkeypatch):
    monkeypatch.setenv("GLM_API_URL", "http://localhost")
    monkeypatch.setenv("GLM_API_KEY", "key")
    monkeypatch.setenv("HF_TOKEN", "token")
    env_validation.check_required(["GLM_API_URL", "GLM_API_KEY", "HF_TOKEN"])


def test_check_required_missing(monkeypatch):
    monkeypatch.delenv("GLM_API_URL", raising=False)
    monkeypatch.setenv("GLM_API_KEY", "key")
    monkeypatch.setenv("HF_TOKEN", "token")
    with pytest.raises(SystemExit) as exc:
        env_validation.check_required(["GLM_API_URL", "GLM_API_KEY", "HF_TOKEN"])
    assert "GLM_API_URL" in str(exc.value)


def test_check_optional_packages_warns(monkeypatch, caplog):
    def fake_import(name):
        if name == "missing":
            raise ImportError("nope")
        return object()

    monkeypatch.setattr(env_validation.importlib, "import_module", fake_import)
    with caplog.at_level(logging.WARNING):
        env_validation.check_optional_packages(["missing", "present"])
    assert any("missing" in r.message for r in caplog.records)


def test_check_optional_packages_ok(monkeypatch, caplog):
    monkeypatch.setattr(env_validation.importlib, "import_module", lambda n: None)
    with caplog.at_level(logging.WARNING):
        env_validation.check_optional_packages(["a", "b"])
    assert not caplog.records


def test_check_required_binaries_ok(monkeypatch):
    monkeypatch.setattr(env_validation.shutil, "which", lambda n: "/usr/bin/" + n)
    env_validation.check_required_binaries(["ffmpeg", "sox"])


def test_check_required_binaries_missing(monkeypatch):
    monkeypatch.setattr(env_validation.shutil, "which", lambda n: None)
    with pytest.raises(SystemExit) as exc:
        env_validation.check_required_binaries(["ffmpeg", "sox"])
    assert "ffmpeg, sox" in str(exc.value)


def test_check_audio_binaries_required(monkeypatch):
    monkeypatch.setattr(env_validation.shutil, "which", lambda n: None)
    with pytest.raises(SystemExit):
        env_validation.check_audio_binaries(require=True)


def test_check_audio_binaries_optional(monkeypatch, caplog):
    monkeypatch.setattr(env_validation.shutil, "which", lambda n: None)
    with caplog.at_level(logging.WARNING):
        ok = env_validation.check_audio_binaries(require=False)
    assert not ok
    assert "Missing optional audio" in caplog.text
