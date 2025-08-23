from __future__ import annotations

"""Utilities for running tests inside an isolated sandbox."""

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Sequence

from . import sandbox_session, virtual_env_manager


@dataclass
class SandboxTestResult:
    """Result returned by :func:`run_pytest`."""

    status: str
    output: str
    sandbox_path: Path


def run_pytest(
    repo_root: Path,
    pytest_args: Sequence[str],
    patch_text: str | None = None,
    sync_on_success: bool = False,
) -> SandboxTestResult:
    """Run ``pytest`` in a sandboxed clone of *repo_root*.

    Parameters
    ----------
    repo_root:
        Path to the original repository.
    pytest_args:
        Arguments passed to ``pytest``.
    patch_text:
        Optional unified diff to apply inside the sandbox before testing.
    sync_on_success:
        If ``True``, apply changes from the sandbox back to ``repo_root`` when
        tests pass.
    """
    sandbox = sandbox_session.create_sandbox(repo_root, virtual_env_manager)
    try:
        if patch_text:
            sandbox_session.apply_patch(sandbox, patch_text)
        _allow_tests(sandbox, pytest_args)
        sandbox_session.install_packages(sandbox, ["pytest"])
        cp = virtual_env_manager.run(
            sandbox / ".venv", ["pytest", *pytest_args], cwd=sandbox
        )
        if sync_on_success:
            diff = subprocess.run(
                ["git", "diff"],
                cwd=sandbox,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            if diff:
                subprocess.run(
                    ["git", "apply"],
                    cwd=repo_root,
                    input=diff,
                    text=True,
                    check=True,
                )
        return SandboxTestResult("pass", cp.stdout, sandbox)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - cleanup path
        output = (exc.stdout or "") + (exc.stderr or "")
        shutil.rmtree(sandbox, ignore_errors=True)
        return SandboxTestResult("fail", output, sandbox)


def _allow_tests(sandbox_root: Path, pytest_args: Sequence[str]) -> None:
    """Ensure tests in *pytest_args* are whitelisted in sandbox ``conftest``."""

    conftest = sandbox_root / "tests" / "conftest.py"
    if not conftest.exists():
        return
    text = conftest.read_text()
    if "ALLOWED_TESTS" not in text:
        return
    lines: list[str] = []
    for arg in pytest_args:
        p = Path(arg)
        if p.suffix == ".py":
            line = f'    str(ROOT / "tests" / "{p.name}"),\n'
            if line not in text and line not in lines:
                lines.append(line)
    if not lines:
        return
    start = text.index("ALLOWED_TESTS = {") + len("ALLOWED_TESTS = {")
    end = text.index("}", start)
    conftest.write_text(text[:end] + "".join(lines) + text[end:])
