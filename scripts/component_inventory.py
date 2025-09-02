# pydocstyle: skip-file

"""Collect metadata for each Python component in the repository.

Run from the repository root::

    python scripts/component_inventory.py

The script scans every ``.py`` file, gathers basic metadata and computes a
quality score. Results are written to three files under ``docs``:

* ``component_status.md`` – table with version, score and last update date.
* ``component_index.md`` – file index with descriptions and dependencies.
* ``component_status.json`` – JSON snapshot for historical comparisons.
"""

from __future__ import annotations

__version__ = "0.1.0"

import ast
import json
import subprocess
import sys
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_MD = REPO_ROOT / "docs" / "component_status.md"
INDEX_MD = REPO_ROOT / "docs" / "component_index.md"
SNAPSHOT_JSON = REPO_ROOT / "docs" / "component_status.json"
INDEX_JSON = REPO_ROOT / "component_index.json"
COVERAGE_SVG = REPO_ROOT / "coverage.svg"
CONNECTOR_INDEX = REPO_ROOT / "docs" / "connectors" / "CONNECTOR_INDEX.md"


@dataclass
class ComponentInfo:
    """Basic metadata for a Python component."""

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
        """Compute a simple completeness score."""
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
    """Yield all Python files in the repository."""
    for path in REPO_ROOT.rglob("*.py"):
        if ".git" in path.parts:
            continue
        yield path


def extract_version(tree: ast.AST) -> str:
    """Return the ``__version__`` value from ``tree`` if present."""
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__version__":
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str
                    ):
                        return node.value.value
    return "0.0.0"


def gather_optional_deps(tree: ast.AST) -> set[str]:
    """Collect modules imported in ``try/except ImportError`` blocks."""
    optional: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            if not any(
                isinstance(h.type, ast.Name) and h.type.id == "ImportError"
                for h in node.handlers
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
    """Collect imported modules excluding optional ones."""
    deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            deps.add(node.module.split(".")[0])
    return deps


def has_type_hints(tree: ast.AST) -> bool:
    """Return ``True`` if the AST contains type annotations."""
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
    """Return ``True`` if a corresponding test file exists."""
    stem = path.stem
    for test in test_files:
        if test.stem == f"test_{stem}":
            return True
    return False


def analyse_file(
    path: Path,
    test_files: list[Path],
    internal: set[str],
    stdlib: set[str],
) -> ComponentInfo:
    """Analyze ``path`` and return component metadata."""
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
    """Return the date of the most recent commit touching ``path``."""
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
    """Write a status table summarizing components."""
    header = (
        "# Component Status\n\nGenerated by " "`scripts/component_inventory.py`.\n\n"
    )
    table_header = (
        "| Path | Version | Score | Last Update |\n| --- | --- | --- | --- |\n"
    )
    lines = [header, table_header]
    for row in rows:
        rel = row.path.relative_to(REPO_ROOT).as_posix()
        lines.append(f"| `{rel}` | {row.version} | {row.score} | {row.last_update} |\n")
    STATUS_MD.write_text("".join(lines), encoding="utf-8")


def write_index_markdown(rows: list[ComponentInfo]) -> None:
    """Write an index of components and their dependencies."""
    header = (
        "# Component Index\n\nGenerated automatically. Lists each Python "
        "file with its description and external dependencies.\n\n"
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
    """Write a JSON snapshot of component scores and versions."""
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


def parse_coverage_svg(path: Path) -> float:
    """Extract coverage percentage from an SVG badge."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return 0.0
    match = re.search(r">(\d+)%<", text)
    return float(match.group(1)) if match else 0.0


def update_coverage(index_path: Path, coverage: float) -> None:
    """Update each component's coverage metric in the index."""
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return
    for component in data.get("components", []):
        metrics = component.setdefault("metrics", {})
        metrics["coverage"] = coverage
    index_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def verify_component_versions(index_path: Path) -> None:
    """Ensure component versions match their module declarations."""
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return
    mismatches: list[str] = []
    missing: list[str] = []
    for component in data.get("components", []):
        rel = component.get("path", "")
        comp_path = REPO_ROOT / rel
        if comp_path.is_dir():
            comp_path = comp_path / "__init__.py"
        if not comp_path.exists():
            continue
        try:
            tree = ast.parse(comp_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        version = extract_version(tree)
        if version == "0.0.0":
            missing.append(f"{component.get('id')}: missing __version__ in {rel}")
        elif version != component.get("version"):
            mismatches.append(
                f"{component.get('id')}: {version} != {component.get('version')}"
            )
    messages: list[str] = []
    if missing:
        messages.append("Missing __version__ declarations:\n" + "\n".join(missing))
    if mismatches:
        messages.append(
            "Version mismatch with component_index.json:\n" + "\n".join(mismatches)
        )
    if messages:
        raise SystemExit("\n\n".join(messages))


def verify_connector_registry(index_path: Path) -> None:
    """Ensure connector registry entries exist and versions align."""
    try:
        text = index_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    mismatches: list[str] = []
    missing: list[str] = []
    registered_paths: set[Path] = set()
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("| id "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        connector_id = cells[0].strip("`")
        version = cells[2]
        code_cell = cells[7]
        match = re.search(r"\(([^)]+)\)", code_cell)
        if not match:
            continue
        rel_path = match.group(1)
        abs_path = (index_path.parent / rel_path).resolve()
        registered_paths.add(abs_path)
        if not abs_path.exists():
            missing.append(f"{connector_id}: missing file {rel_path}")
            continue
        try:
            tree = ast.parse(abs_path.read_text(encoding="utf-8"))
        except Exception:
            missing.append(f"{connector_id}: unreadable file {rel_path}")
            continue
        module_version = extract_version(tree)
        if module_version == "0.0.0":
            missing.append(f"{connector_id}: missing __version__ in {rel_path}")
        elif module_version != version:
            mismatches.append(
                f"{connector_id}: {module_version} != {version} ({rel_path})"
            )
    connector_dir = REPO_ROOT / "connectors"
    for file in connector_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
        if file.resolve() not in registered_paths:
            missing.append(
                f"unregistered connector: {file.relative_to(REPO_ROOT).as_posix()}"
            )
    messages: list[str] = []
    if missing:
        messages.append("Connector registry issues:\n" + "\n".join(missing))
    if mismatches:
        messages.append("Connector version mismatches:\n" + "\n".join(mismatches))
    if messages:
        raise SystemExit("\n\n".join(messages))


def main() -> None:
    """Generate component inventory artifacts."""
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
    coverage = parse_coverage_svg(COVERAGE_SVG)
    update_coverage(INDEX_JSON, coverage)
    verify_component_versions(INDEX_JSON)
    verify_connector_registry(CONNECTOR_INDEX)


if __name__ == "__main__":
    main()
