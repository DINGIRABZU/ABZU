"""Tests for tools.dependency_installer via sandbox_session."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tools import virtual_env_manager
from tools.sandbox_session import create_sandbox, install_packages

PACKAGE = "pyjokes"


def test_install_packages_only_in_sandbox() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sandbox = create_sandbox(repo_root, virtual_env_manager)

    # ensure host doesn't have package
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(PACKAGE)

    install_packages(sandbox, [PACKAGE])

    # package imports inside sandbox
    virtual_env_manager.run(sandbox / ".venv", ["python", "-c", f"import {PACKAGE}"])

    # still absent on host
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(PACKAGE)
