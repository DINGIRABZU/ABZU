"""Rebuild RAZAR modules from documentation references.

This utility scans project documentation and the system blueprint for links to
Python modules.  For every referenced module that appears in the planning
specification produced by :mod:`agents.razar.planning_engine`, a fresh skeleton
module is generated using :mod:`agents.razar.module_builder`.

The generated modules are placed inside a new workspace directory so that the
original repository remains untouched.  This is primarily intended for recovery
or "from scratch" rebuild scenarios where a clean project tree must be
reconstructed from the docs alone.
"""

from __future__ import annotations

__version__ = "0.2.2"

from pathlib import Path
import re
import shutil
import tempfile
from typing import Iterable, List

from . import planning_engine, module_builder

_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.py)\)")


def _ensure_packages(base: Path, module_path: Path) -> None:
    """Create ``__init__`` files for ``module_path`` relative to ``base``."""

    current = module_path.parent
    while True:
        init_file = current / "__init__.py"
        init_file.touch(exist_ok=True)
        if current == base:
            break
        current = current.parent


def _extract_module_names(text: str) -> List[str]:
    """Return module names referenced by markdown links in ``text``."""

    modules: List[str] = []
    for match in _LINK_RE.finditer(text):
        link = match.group(1).strip()
        if link.startswith("../"):
            link = link[3:]
        link = link.lstrip("./")
        modules.append(Path(link).stem)
    return modules


def _collect_modules(paths: Iterable[Path]) -> List[str]:
    """Collect unique module names from a sequence of markdown ``paths``."""

    found: List[str] = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        found.extend(_extract_module_names(text))
    return sorted(set(found))


def bootstrap_from_docs(
    *,
    docs_dir: Path | None = None,
    blueprint: Path | None = None,
    workspace: Path | None = None,
) -> List[Path]:
    """Regenerate modules referenced in project documentation.

    Parameters
    ----------
    docs_dir:
        Directory containing markdown documentation.  All ``*.md`` files within
        this directory are scanned for links to Python modules.  Defaults to the
        repository's ``docs`` directory.
    blueprint:
        Optional explicit path to ``system_blueprint.md``.  When provided and not
        already inside ``docs_dir``, it is included in the scan.
    workspace:
        Target directory that will receive the reconstructed modules.  When not
        specified, a temporary directory is created.

    Returns
    -------
    list[pathlib.Path]
        Paths to the generated modules inside ``workspace``.
    """

    repo_root = Path(__file__).resolve().parents[2]
    docs_dir = docs_dir or repo_root / "docs"
    blueprint = blueprint or docs_dir / "system_blueprint.md"
    workspace = workspace or Path(tempfile.mkdtemp(prefix="razar_retro_"))

    docs = list(docs_dir.glob("*.md"))
    if blueprint not in docs:
        docs.append(blueprint)

    modules = _collect_modules(docs)
    plan = planning_engine.plan()

    generated: List[Path] = []
    for name in modules:
        spec = plan.get(name)
        if spec is None:
            continue
        built = module_builder.build(name, plan=plan)
        rel = Path(str(spec.get("component", "")))
        target = workspace / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        _ensure_packages(workspace, target)
        shutil.move(str(built), target)
        generated.append(target)
    return generated


__all__ = ["bootstrap_from_docs"]
