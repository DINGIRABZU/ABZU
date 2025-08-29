#!/usr/bin/env python3
"""Verify module __version__ values against component_index.json."""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "component_index.json"


def extract_version(file_path: Path) -> str | None:
    """Return the __version__ string defined in file_path or None."""
    if not file_path.exists():
        return None
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__version__":
                    value = node.value
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        return value.value
    return None


def main() -> int:
    """Compare module versions to the index and return process status."""
    index = json.loads(INDEX_PATH.read_text())
    mismatches: list[str] = []
    for comp in index.get("components", []):
        path = ROOT / comp["path"]
        module_file = path / "__init__.py" if path.is_dir() else path
        version = extract_version(module_file)
        if version != comp.get("version"):
            mismatches.append(
                f"{comp['id']}: index {comp['version']} != module {version}"
            )
    if mismatches:
        for line in mismatches:
            print(line)
        return 1
    print("All component versions match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
