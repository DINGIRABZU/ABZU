"""Run code patches in an isolated sandbox and execute tests."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from tools import sandbox_session, virtual_env_manager

logger = logging.getLogger(__name__)


def run_sandbox(patch_path_str: str) -> None:
    """Apply a patch file in a sandbox and run tests."""
    if not patch_path_str:
        print("Usage: /sandbox <patch-file>")
        return
    patch_file = Path(patch_path_str)
    try:
        patch_text = patch_file.read_text()
    except Exception as exc:
        logger.error("Unable to read patch file: %s", exc)
        return
    repo_root = Path(__file__).resolve().parents[1]
    try:
        sandbox_root = sandbox_session.create_sandbox(repo_root, virtual_env_manager)
        sandbox_session.apply_patch(sandbox_root, patch_text)
        env = sandbox_root / ".venv"
        req_file = sandbox_root / "tests" / "requirements.txt"
        virtual_env_manager.install_requirements(env, req_file)
        try:
            result = virtual_env_manager.run(env, ["pytest"], cwd=sandbox_root)
            print(result.stdout)
            print("Sandbox tests passed.")
        except subprocess.CalledProcessError as exc:
            logger.error("%s", exc.stdout)
            logger.error("%s", exc.stderr)
            logger.error("Sandbox tests failed.")
    except Exception as exc:
        logger.error("Sandbox error: %s", exc)


__all__ = ["run_sandbox"]
