"""Utilities for constructing new RAZAR modules.

This helper consumes component specifications produced by
:mod:`agents.razar.planning_engine` and prepares a fresh module in an isolated
sandbox directory.  A template or implementation snippet must seed the
module—``TODO`` placeholders are no longer written by default.

Remote RAZAR agents may provide patch suggestions which are applied inside the
sandbox before running the unit tests included in the specification.  Only when
these tests succeed is the generated module promoted into the repository's main
source tree.
"""

from __future__ import annotations

__version__ = "0.2.2"

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Iterable, Mapping, Tuple
import os

from . import doc_sync, planning_engine, remote_loader


def _write_boilerplate(
    path: Path,
    *,
    template: str | Path | None = None,
    snippet: str | None = None,
) -> None:
    """Create a new module at ``path`` using ``template`` or ``snippet``.

    Exactly one of ``template`` or ``snippet`` must be provided. ``template``
    is interpreted as a filesystem path whose content seeds the new module;
    ``snippet`` writes inline code directly.  A ``ValueError`` is raised when
    neither or both options are supplied.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if template and snippet:
        raise ValueError("Provide either template or snippet, not both")
    if template:
        content = Path(template).read_text(encoding="utf-8")
    elif snippet:
        content = snippet
    else:  # pragma: no cover - defensive
        raise ValueError("Implementation snippet or template required")
    path.write_text(content, encoding="utf-8")


def _apply_patch(path: Path, suggestion: Mapping[str, str]) -> None:
    """Apply a patch ``suggestion`` to ``path``.

    The suggestion format mirrors the structure returned by
    :func:`remote_loader.load_remote_agent` where ``suggestion`` is expected to
    contain ``file`` and ``content`` keys.  ``file`` is resolved relative to the
    sandbox root and defaults to ``path`` when omitted.  ``content`` is appended
    to the target file.
    """
    target = suggestion.get("file")
    content = suggestion.get("content")
    if not content:
        return
    target_path = path if target is None else path.parent / target
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("a", encoding="utf-8") as fh:
        fh.write(content)


def build(
    component_name: str,
    *,
    plan: Mapping[str, Mapping[str, object]] | None = None,
    remote_agents: Iterable[Tuple[str, str]] | None = None,
) -> Path:
    """Generate and promote ``component_name`` according to ``plan``.

    Parameters
    ----------
    component_name:
        Key within the planning specification identifying the component to
        generate.
    plan:
        Mapping produced by :func:`planning_engine.plan`.  When ``None``, a fresh
        plan is computed.  Only the entry for ``component_name`` is used.  The
        component specification must include either ``template`` (path to a
        file) or ``snippet`` (inline source) to seed the module.
    remote_agents:
        Optional iterable of ``(name, url)`` tuples designating remote agents
        that may return patch suggestions.

    Returns
    -------
    pathlib.Path
        Final location of the promoted module in the repository tree.
    """
    repo_root = Path(__file__).resolve().parents[2]
    plan = plan or planning_engine.plan()
    spec = plan.get(component_name)
    if spec is None or not isinstance(spec, Mapping):
        raise KeyError(f"Component {component_name!r} not found in plan")

    component_rel = Path(str(spec.get("component", "")))
    sandbox = Path(tempfile.mkdtemp(prefix="razar_module_"))
    module_path = sandbox / component_rel
    template: str | Path | None = spec.get("template")  # type: ignore[assignment]
    snippet: str | None = spec.get("snippet")  # type: ignore[assignment]
    _write_boilerplate(module_path, template=template, snippet=snippet)

    for name, url in list(remote_agents or []):
        _module, _config, suggestion = remote_loader.load_remote_agent(
            name, url, patch_context=str(module_path)
        )
        if isinstance(suggestion, Mapping):
            _apply_patch(module_path, suggestion)

    tests: Mapping[str, str] = spec.get("tests", {})  # type: ignore[assignment]
    for rel, content in tests.items():
        test_path = sandbox / rel
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(content, encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(sandbox)
    try:
        subprocess.run(
            [
                "pytest",
                "-q",
            ],
            cwd=sandbox,
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Unit tests failed for component {component_name}") from exc

    final_path = repo_root / component_rel
    final_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(module_path), final_path)
    shutil.rmtree(sandbox, ignore_errors=True)
    doc_sync.sync_docs()
    return final_path
