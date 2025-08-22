from __future__ import annotations

"""Helpers for working with sandboxed repository copies."""

from pathlib import Path
import subprocess
import tempfile


def create_sandbox(repo_root: Path, env_manager) -> Path:
    """Copy *repo_root* into a temporary directory and set up a venv.

    The repository is cloned into a fresh temporary directory and a virtual
    environment is created inside it using *env_manager*.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="sandbox-"))
    sandbox_root = temp_dir / repo_root.name
    subprocess.run(["git", "clone", str(repo_root), str(sandbox_root)], check=True)
    env_path = sandbox_root / ".venv"
    env_manager.create_env(env_path)
    return sandbox_root


def apply_patch(sandbox_root: Path, patch_text: str) -> None:
    """Apply a unified diff *patch_text* to the sandbox repository."""
    subprocess.run(
        ["git", "apply"],
        cwd=sandbox_root,
        input=patch_text,
        text=True,
        check=True,
    )
