from __future__ import annotations

"""Utilities for working with Python virtual environments."""

from pathlib import Path
import os
import subprocess
import sys
from typing import Sequence


def _bin_dir(env: Path) -> Path:
    """Return the scripts directory for the virtual environment."""
    return env / ("Scripts" if os.name == "nt" else "bin")


def create_env(path: Path) -> None:
    """Create a virtual environment at *path* using ``python -m venv``."""
    subprocess.run([sys.executable, "-m", "venv", str(path)], check=True)


def install_requirements(env: Path, requirements_file: Path) -> None:
    """Install packages listed in *requirements_file* into *env*."""
    run(env, ["pip", "install", "-r", str(requirements_file)])


def run(env: Path, command: Sequence[str] | str, **kwargs) -> subprocess.CompletedProcess:
    """Execute *command* inside *env*.

    Returns the ``subprocess.CompletedProcess`` instance. Additional keyword
    arguments are forwarded to ``subprocess.run``.
    """
    env_vars = os.environ.copy()
    bin_path = _bin_dir(env)
    env_vars["VIRTUAL_ENV"] = str(env)
    env_vars["PATH"] = f"{bin_path}{os.pathsep}" + env_vars.get("PATH", "")
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("check", True)
    return subprocess.run(command, env=env_vars, **kwargs)
