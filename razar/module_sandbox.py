from __future__ import annotations

__version__ = "0.1.0"

"""Temporary sandbox for module patches from CROWN.

This helper clones selected components into a temporary directory, applies
patches or file scaffolds suggested by CROWN, runs ``pytest`` on the affected
modules and only promotes the changes back to the working tree when tests pass.

Example::

    python -m razar.module_sandbox path/to/module --patch response.diff
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def clone_repository() -> Path:
    """Return path to a sandbox copy of the repository."""

    repo_root = Path.cwd()
    sandbox_root = Path(tempfile.mkdtemp(prefix="module_sandbox_"))
    clone_path = sandbox_root / repo_root.name
    shutil.copytree(repo_root, clone_path, ignore=shutil.ignore_patterns(".git"))
    return clone_path


def _read_patches(paths: Sequence[Path]) -> List[str]:
    patches: List[str] = []
    for path in paths:
        patches.append(path.read_text(encoding="utf-8"))
    return patches


def _parse_scaffolds(entries: Sequence[str]) -> Dict[str, Path]:
    scaffolds: Dict[str, Path] = {}
    for entry in entries:
        src, _, dest = entry.partition(":")
        scaffolds[dest] = Path(src)
    return scaffolds


def apply_patches(sandbox: Path, patches: Iterable[str]) -> None:
    """Apply unified diff patches inside ``sandbox``."""

    for patch in patches:
        subprocess.run(
            ["patch", "-p1"], input=patch, text=True, cwd=sandbox, check=True
        )


def apply_scaffolds(sandbox: Path, scaffolds: Dict[str, Path]) -> None:
    """Copy scaffold files into ``sandbox`` relative to repository root."""

    for dest_rel, src_path in scaffolds.items():
        dest = sandbox / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")


def run_tests(sandbox: Path, modules: Sequence[str]) -> bool:
    """Run ``pytest`` for ``modules`` within ``sandbox``."""

    cmd = ["pytest", *modules]
    proc = subprocess.run(cmd, cwd=sandbox)
    return proc.returncode == 0


def promote_changes(sandbox: Path, modules: Sequence[str]) -> None:
    """Copy updated ``modules`` from ``sandbox`` to the working tree."""

    repo_root = Path.cwd()
    for module in modules:
        src = sandbox / module
        dest = repo_root / module
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def main() -> None:  # pragma: no cover - CLI helper
    parser = argparse.ArgumentParser(description="Sandbox component changes.")
    parser.add_argument("modules", nargs="+", help="Component paths to sandbox")
    parser.add_argument(
        "--patch", action="append", type=Path, default=[], help="Patch file to apply"
    )
    parser.add_argument(
        "--scaffold",
        action="append",
        default=[],
        metavar="SRC:DEST",
        help="Copy SRC file to DEST path inside sandbox",
    )
    args = parser.parse_args()

    sandbox = clone_repository()
    try:
        patches = _read_patches(args.patch)
        scaffolds = _parse_scaffolds(args.scaffold)
        apply_patches(sandbox, patches)
        apply_scaffolds(sandbox, scaffolds)
        ok = run_tests(sandbox, args.modules)
        if ok:
            promote_changes(sandbox, args.modules)
        else:
            print("Tests failed; discarding sandbox changes.")
    finally:
        shutil.rmtree(sandbox.parent, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
