"""Automated module repair using LLM patch suggestions.

This helper collects context around failing modules, requests patch suggestions
from the CROWN LLM (or alternate models) and evaluates the patches inside a
sandbox. When the patched module passes its tests the change is reintroduced and
the component is reactivated.
"""

from __future__ import annotations

__version__ = "0.1.0"

import difflib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from INANNA_AI.glm_integration import GLMIntegration

from . import doc_sync, quarantine_manager

logger = logging.getLogger(__name__)

# Determine repository root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PATCH_LOG_PATH = PROJECT_ROOT / "logs" / "razar_ai_patches.json"


def _record_patch(component: str, diff: str, tests: str) -> None:
    """Append a patch record to ``PATCH_LOG_PATH``."""
    PATCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {"component": component, "diff": diff, "tests": tests}
    if PATCH_LOG_PATH.exists():
        try:
            data = json.loads(PATCH_LOG_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except json.JSONDecodeError:
            data = []
    else:
        data = []
    data.append(record)
    PATCH_LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _gather_context(module_path: Path, error: str) -> str:
    """Return a textual context block for ``module_path`` and ``error``."""
    source = module_path.read_text(encoding="utf-8")
    return f"""Repair the following module.\n\nError:\n{error}\n\nCode:\n{source}\n"""


def _request_patch(context: str, models: Sequence[GLMIntegration]) -> str:
    """Return patch text by querying ``models`` in order."""
    for model in models:
        suggestion = model.complete(context)
        if suggestion and "unavailable" not in suggestion.lower():
            return suggestion
    return ""


def _run_tests(test_paths: Iterable[Path], env: dict[str, str]) -> bool:
    """Execute ``pytest`` for ``test_paths`` with ``env``."""
    cmd = ["pytest", *map(str, test_paths)]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, text=True)
    if result.returncode != 0:
        logger.error("Tests failed with code %s", result.returncode)
        return False
    return True


def _apply_patch(
    module_path: Path, patch_text: str, test_paths: Sequence[Path]
) -> bool:
    """Apply ``patch_text`` in a sandbox and run tests."""
    original = module_path.read_text(encoding="utf-8")
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(),
            patch_text.splitlines(),
            fromfile=str(module_path),
            tofile=str(module_path),
            lineterm="",
        )
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox_root = Path(tmpdir)
        rel = module_path.relative_to(PROJECT_ROOT)
        target = sandbox_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(patch_text, encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(sandbox_root) + os.pathsep + env.get("PYTHONPATH", "")

        if not _run_tests(test_paths, env):
            return False

        shutil.copy2(target, module_path)
    quarantine_manager.reactivate_component(
        module_path.stem, verified=True, automated=True
    )
    _record_patch(module_path.stem, diff, "passed")
    doc_sync.sync_docs()
    return True


def repair_module(
    module_path: Path,
    tests: Sequence[Path],
    error: str,
    *,
    models: Sequence[GLMIntegration] | None = None,
) -> bool:
    """Attempt to repair ``module_path`` using ``tests`` and ``error`` context.

    Parameters
    ----------
    module_path:
        Path to the failing module.
    tests:
        Test file paths verifying the module's behaviour.
    error:
        Error message from the failing test run.
    models:
        Optional ordered list of models to query for patch suggestions. When
        omitted, a single default :class:`GLMIntegration` is used.
    """
    if models is None:
        models = [GLMIntegration()]

    context = _gather_context(module_path, error)
    patch = _request_patch(context, models)
    if not patch:
        logger.error("No patch suggestion received")
        return False
    return _apply_patch(module_path, patch, tests)


__all__ = ["repair_module", "PATCH_LOG_PATH"]
