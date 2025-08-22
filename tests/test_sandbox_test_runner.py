"""Tests for tools.sandbox_test_runner."""

from __future__ import annotations

import subprocess
from pathlib import Path

import conftest as conftest_module

from tools.sandbox_test_runner import run_pytest

# Allow this test module to run under the constrained test selection
conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))


def _git_status(path: Path) -> str:
    cp = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    )
    return cp.stdout.strip()


def test_run_pytest_success_returns_pass() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    patch = (
        "diff --git a/tests/dummy_pass_test.py b/tests/dummy_pass_test.py\n"
        "new file mode 100644\n"
        "index 0000000..e69de29\n"
        "--- /dev/null\n"
        "+++ b/tests/dummy_pass_test.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def test_dummy_pass():\n"
        "+    assert True\n"
    )
    result = run_pytest(repo_root, ["tests/dummy_pass_test.py"], patch)
    assert result.status == "pass"


def test_run_pytest_failure_cleans_repo() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    before_status = _git_status(repo_root)
    patch = (
        "diff --git a/NEW_FILE.txt b/NEW_FILE.txt\n"
        "new file mode 100644\n"
        "index 0000000..e69de29\n"
        "--- /dev/null\n"
        "+++ b/NEW_FILE.txt\n"
        "@@ -0,0 +1 @@\n"
        "+sandbox change\n"
        "diff --git a/tests/dummy_fail_test.py b/tests/dummy_fail_test.py\n"
        "new file mode 100644\n"
        "index 0000000..e69de29\n"
        "--- /dev/null\n"
        "+++ b/tests/dummy_fail_test.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def test_dummy_fail():\n"
        "+    assert False\n"
    )
    result = run_pytest(repo_root, ["tests/dummy_fail_test.py"], patch)
    assert result.status == "fail"
    assert not result.sandbox_path.exists()
    assert _git_status(repo_root) == before_status
    assert not (repo_root / "NEW_FILE.txt").exists()
