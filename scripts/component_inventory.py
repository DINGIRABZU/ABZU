from __future__ import annotations

"""Collect metadata for each Python component in the repository.

Run from the repository root::

    python scripts/component_inventory.py

The script scans every ``.py`` file, gathers basic metadata and computes a
quality score. Results are written to three files under ``docs``:

* ``component_status.md`` – table with version, score and last update date.
* ``component_index.md`` – file index with descriptions and dependencies.
* ``component_status.json`` – JSON snapshot for historical comparisons.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import ast
import json
import subprocess
import sys
from typing import Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_MD = REPO_ROOT / "docs" / "component_status.md"
INDEX_MD = REPO_ROOT / "docs" / "component_index.md"
SNAPSHOT_JSON = REPO_ROOT / "docs" / "component_status.json"


@dataclass
class ComponentInfo:
    path: Path
    description: str
    dependencies: set[str]
    optional_dependencies: set[str]
    has_type_hints: bool
    has_tests: bool
    version: str
    last_update: str

    @property
    def score(self) -> int:
        score = 0
        if self.description:
            score += 1
        if self.has_type_hints:
            score += 1
        if self.has_tests:
            score += 1
        if self.optional_dependencies:
            score += 1
        return score


def iter_py_files() -> Iterator[Path]:
    for path in REPO_ROOT.rglob("*.py"):
        if ".git" in path.parts:
            continue
        yield path


def extract_version(tree: ast.AST) -> str:
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__version__":
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return node.value.value
    return "0.0.0"


def gather_optional_deps(tree: ast.AST) -> set[str]:
    optional: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            if not any(
                isinstance(h.type, ast.Name) and h.type.id == "ImportError" for h in node.handlers
            ):
                continue
            for body_node in node.body:
                if isinstance(body_node, ast.Import):
                    for alias in body_node.names:
                        optional.add(alias.name.split(".")[0])
                elif isinstance(body_node, ast.ImportFrom) and body_node.module:
                    optional.add(body_node.module.split(".")[0])
    return optional


def gather_dependencies(tree: ast.AST) -> set[str]:
    deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            deps.add(node.module.split(".")[0])
    return deps


def has_type_hints(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                return True
            for arg in list(node.args.args) + list(node.args.kwonlyargs):
                if arg.annotation is not None:
                    return True
    return False


def has_tests_for(path: Path, test_files: list[Path]) -> bool:
    stem = path.stem
    for test in test_files:
        if test.stem == f"test_{stem}":
            return True
    return False


def analyse_file(path: Path, test_files: list[Path], internal: set[str], stdlib: set[str]) -> ComponentInfo:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        tree = ast.parse("")
    doc = ast.get_docstring(tree) or ""
    description = doc.splitlines()[0] if doc else ""
    version = extract_version(tree)
    deps = gather_dependencies(tree)
    optional = gather_optional_deps(tree)
    deps -= optional
    deps = {d for d in deps if d not in internal and d not in stdlib}
    optional = {d for d in optional if d not in internal and d not in stdlib}
    info = ComponentInfo(
        path=path,
        description=description,
        dependencies=deps,
        optional_dependencies=optional,
        has_type_hints=has_type_hints(tree),
        has_tests=has_tests_for(path, test_files),
        version=version,
        last_update=git_last_update(path),
    )
    return info


def git_last_update(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", str(path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() or ""
    except Exception:
        return ""


def write_status_markdown(rows: list[ComponentInfo]) -> None:
    header = "# Component Status\n\nGenerated by `scripts/component_inventory.py`.\n\n"
    table_header = "| Path | Version | Score | Last Update |\n| --- | --- | --- | --- |\n"
    lines = [header, table_header]
    for row in rows:
        rel = row.path.relative_to(REPO_ROOT).as_posix()
        lines.append(
            f"| `{rel}` | {row.version} | {row.score} | {row.last_update} |\n"
        )
    STATUS_MD.write_text("".join(lines), encoding="utf-8")


def write_index_markdown(rows: list[ComponentInfo]) -> None:
    header = (
        "# Component Index\n\nGenerated automatically. Lists each Python file with its description and external dependencies.\n\n"
    )
    table_header = "| File | Description | Dependencies |\n| --- | --- | --- |\n"
    lines = [header, table_header]
    for row in rows:
        rel = row.path.relative_to(REPO_ROOT).as_posix()
        desc = row.description or "No description"
        deps = sorted(row.dependencies | row.optional_dependencies)
        dep_str = ", ".join(deps) if deps else "None"
        lines.append(f"| `{rel}` | {desc} | {dep_str} |\n")
    INDEX_MD.write_text("".join(lines), encoding="utf-8")


def write_json_snapshot(rows: list[ComponentInfo]) -> None:
    snapshot = {
        "generated": date.today().isoformat(),
        "components": {
            row.path.relative_to(REPO_ROOT).as_posix(): {
                "version": row.version,
                "score": row.score,
                "last_update": row.last_update,
            }
            for row in rows
        },
    }
    SNAPSHOT_JSON.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def main() -> None:
    py_files = list(iter_py_files())
    test_dir = REPO_ROOT / "tests"
    test_files = list(test_dir.rglob("test_*.py")) if test_dir.exists() else []
    internal = {p.stem for p in py_files}
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    rows = [analyse_file(p, test_files, internal, stdlib) for p in py_files]
    rows.sort(key=lambda r: r.path.relative_to(REPO_ROOT).as_posix())
    write_status_markdown(rows)
    write_index_markdown(rows)
    write_json_snapshot(rows)


if __name__ == "__main__":
    main()
