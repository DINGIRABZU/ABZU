"""Tests for tools.virtual_env_manager."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tools.virtual_env_manager import create_env, install_requirements, run


def test_create_env(tmp_path: Path) -> None:
    env_dir = tmp_path / "env"
    create_env(env_dir)
    python_bin = (
        env_dir
        / ("Scripts" if os.name == "nt" else "bin")
        / ("python.exe" if os.name == "nt" else "python")
    )
    assert python_bin.exists()


def test_install_requirements_isolated(tmp_path: Path) -> None:
    env_dir = tmp_path / "env"
    create_env(env_dir)

    pkg_dir = tmp_path / "dummy_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "setup.py").write_text(
        "from setuptools import setup\nsetup(name='dummy_pkg', version='0.0.0')\n"
    )
    (pkg_dir / "dummy_pkg").mkdir()
    (pkg_dir / "dummy_pkg" / "__init__.py").write_text("")

    req_file = tmp_path / "requirements.txt"
    req_file.write_text(str(pkg_dir))
    install_requirements(env_dir, req_file)

    run(env_dir, ["python", "-c", "import dummy_pkg"])
    proc = subprocess.run(
        [sys.executable, "-c", "import dummy_pkg"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_run_isolated_sys_path(tmp_path: Path) -> None:
    env_dir = tmp_path / "env"
    create_env(env_dir)
    cp = run(
        env_dir,
        ["python", "-c", "import sys, json; print(json.dumps(sys.path))"],
    )
    paths = json.loads(cp.stdout.strip())
    site_paths = [p for p in paths if "site-packages" in p]
    assert site_paths
    assert all(p.startswith(str(env_dir)) for p in site_paths)
