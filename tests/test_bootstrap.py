"""Tests for the bootstrap script."""

from __future__ import annotations

import importlib
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts import bootstrap


def test_python_version_check(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 9, 0))
    with pytest.raises(SystemExit):
        bootstrap.check_python()


def test_optional_package_install(monkeypatch):
    missing = {"faiss", "sqlite3"}

    def fake_import(name):
        if name in missing:
            raise ImportError
        return SimpleNamespace()

    calls = []

    def fake_check_call(cmd):
        calls.append(cmd)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    monkeypatch.setattr(subprocess, "check_call", fake_check_call)
    bootstrap.ensure_optional_deps()
    assert [c[-1] for c in calls] == ["faiss-cpu", "pysqlite3-binary"]


def test_env_validation(monkeypatch):
    for var in bootstrap.REQUIRED_VARS:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(SystemExit):
        bootstrap.validate_env()
    for var in bootstrap.REQUIRED_VARS:
        monkeypatch.setenv(var, "x")
    bootstrap.validate_env()
