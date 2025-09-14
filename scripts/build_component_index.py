#!/usr/bin/env python3
"""Generate the component index.

This script walks the repository looking for Python modules that declare a
``__version__`` attribute.  Each discovered module is added to
``component_index.json`` with minimal metadata required by the schema:
``id``, ``chakra``, ``type``, ``path``, ``version``, ``status`` and an
``issues`` field explaining the status rationale.

Status is inferred heuristically:

* ``broken`` – the path is missing.
* ``deprecated`` – the source contains the word ``deprecated``.
* ``experimental`` – the source contains ``experimental`` or the module has
  no associated tests.
* ``active`` – the module exists and has at least one test referencing it.

The resulting JSON is validated elsewhere against
``docs/schemas/component_index.json``.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
import tomllib


RE_VERSION = re.compile(r"__version__\s*=\s*['\"]([^'\"]+)['\"]")
RE_DEPRECATED = re.compile(r"deprecated", re.IGNORECASE)
RE_EXPERIMENTAL = re.compile(r"experimental", re.IGNORECASE)

CHAKRAS = ["root", "sacral", "solar", "heart", "throat", "third_eye", "crown"]


def detect_chakra(path: Path) -> str:
    """Best-effort chakra deduction based on path segments."""

    for chakra in CHAKRAS:
        if chakra in path.parts:
            return chakra
    return "unknown"


def detect_type(path: Path) -> str:
    """Infer a component type from its location."""

    parts = path.parts
    if "agents" in parts:
        return "agent"
    if "connectors" in parts:
        return "connector"
    if "scripts" in parts:
        return "script"
    if "tests" in parts:
        return "test"
    return "module"


def find_tests(component_id: str, component_path: Path) -> list[str]:
    """Return list of test files referencing the component."""

    tests_dir = Path("tests")
    if not tests_dir.exists():
        return []

    pattern = re.compile(rf"\b{re.escape(component_id)}\b")
    matches: list[str] = []
    for test_file in tests_dir.rglob("*.py"):
        try:
            text = test_file.read_text()
        except Exception:  # pragma: no cover - unreadable file
            continue
        if pattern.search(text) or component_path.as_posix() in text:
            matches.append(test_file.relative_to(Path(".")).as_posix())
    return sorted(matches)


def gather_dependencies(text: str) -> list[str]:
    """Extract imported modules from source text."""

    try:
        tree = ast.parse(text)
    except Exception:  # pragma: no cover - parse errors are rare
        return []
    deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            deps.add(node.module.split(".")[0])
    return sorted(deps)


def determine_status(path: Path, text: str, tests: list[str]) -> tuple[str, str]:
    """Determine component status and rationale."""

    if not path.exists():
        return "broken", "Path does not exist"
    if RE_DEPRECATED.search(text):
        return "deprecated", "Marked deprecated in source"
    if RE_EXPERIMENTAL.search(text):
        return "experimental", "Marked experimental in source"
    if tests:
        return "active", "No known issues"
    return "experimental", "No tests found"


def main() -> None:
    repo_root = Path(".")
    components = []

    for py_file in repo_root.rglob("*.py"):
        rel = py_file.relative_to(repo_root)

        # Skip hidden directories and documentation/tests when collecting
        if any(part.startswith(".") for part in rel.parts):
            continue
        if "docs" in rel.parts or "tests" in rel.parts:
            continue

        try:
            text = py_file.read_text()
        except Exception:  # pragma: no cover - unreadable file
            continue

        match = RE_VERSION.search(text)
        if not match:
            continue

        version = match.group(1)
        component_id = (
            py_file.stem if py_file.name != "__init__.py" else py_file.parent.name
        )
        chakra = detect_chakra(rel)
        comp_type = detect_type(rel)
        dependencies = gather_dependencies(text)
        tests = find_tests(component_id, py_file)
        status, issues = determine_status(py_file, text, tests)

        components.append(
            {
                "id": component_id,
                "chakra": chakra,
                "type": comp_type,
                "path": rel.as_posix(),
                "version": version,
                "dependencies": dependencies,
                "tests": tests,
                "metrics": {},
                "status": status,
                "issues": issues,
                "adr": None,
            }
        )

    for cargo_file in repo_root.rglob("Cargo.toml"):
        try:
            cargo_data = tomllib.loads(cargo_file.read_text())
        except Exception:  # pragma: no cover - unreadable file
            continue
        package = cargo_data.get("package")
        if not package:
            continue
        rel_dir = cargo_file.parent.relative_to(repo_root)
        if any(part.startswith(".") for part in rel_dir.parts):
            continue
        if "target" in rel_dir.parts or "node_modules" in rel_dir.parts:
            continue
        crate_id = package.get("name", rel_dir.name)
        version = package.get("version", "0.0.0")
        src_file = cargo_file.parent / "src" / "lib.rs"
        try:
            text = src_file.read_text()
        except Exception:
            text = ""
        dependencies = sorted(cargo_data.get("dependencies", {}).keys())
        tests_dir = cargo_file.parent / "tests"
        tests = (
            [p.relative_to(repo_root).as_posix() for p in tests_dir.rglob("*.rs")]
            if tests_dir.exists()
            else []
        )
        status, issues = determine_status(src_file, text, tests)
        components.append(
            {
                "id": crate_id,
                "chakra": detect_chakra(rel_dir),
                "type": "rust",
                "path": (
                    src_file.relative_to(repo_root).as_posix()
                    if src_file.exists()
                    else rel_dir.as_posix()
                ),
                "version": version,
                "dependencies": dependencies,
                "tests": tests,
                "metrics": {},
                "status": status,
                "issues": issues,
                "adr": None,
            }
        )

    components.sort(key=lambda c: c["id"])

    data = {
        "$schema": "./docs/schemas/component_index.json",
        "components": components,
    }

    Path("component_index.json").write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
