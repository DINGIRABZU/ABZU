"""Tests for tools.sandbox_session."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from tools import virtual_env_manager
from tools.sandbox_session import apply_patch, create_sandbox


def _git_status(path: Path) -> str:
    cp = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    )
    return cp.stdout.strip()


def test_create_sandbox_creates_temp_repo() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sandbox = create_sandbox(repo_root, virtual_env_manager)
    assert sandbox.exists()
    assert sandbox != repo_root
    assert Path(tempfile.gettempdir()) in sandbox.parents
    assert (sandbox / ".venv").exists()


def test_apply_patch_isolated() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sandbox = create_sandbox(repo_root, virtual_env_manager)

    patch = """diff --git a/NEW_FILE.txt b/NEW_FILE.txt\nnew file mode 100644\nindex 0000000..e69de29\n--- /dev/null\n+++ b/NEW_FILE.txt\n@@ -0,0 +1 @@\n+hello sandbox\n"""
    apply_patch(sandbox, patch)

    assert (sandbox / "NEW_FILE.txt").exists()
    assert not (repo_root / "NEW_FILE.txt").exists()
    assert _git_status(repo_root) == ""
    assert _git_status(sandbox) != ""
