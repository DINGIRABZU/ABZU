#!/usr/bin/env python3
"""Verify modules have corresponding tests and docs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

COMPONENT_STATUS = Path("docs/component_status.json")
DOCS_DIR = Path("docs")
TESTS_DIR = Path("tests")


def main() -> None:
    data = json.loads(COMPONENT_STATUS.read_text())
    components = data.get("components", {})
    missing: list[str] = []

    for path in components:
        if path.startswith("tests/") or path.startswith("docs/"):
            continue
        module_path = Path(path)
        base = module_path.stem
        test_file = TESTS_DIR / f"test_{base}.py"
        doc_exists = any(base in doc.stem for doc in DOCS_DIR.rglob("*.md"))
        test_exists = test_file.exists()

        issues = []
        if not test_exists:
            issues.append("tests")
        if not doc_exists:
            issues.append("docs")
        if issues:
            missing.append(f"{path} missing {' and '.join(issues)}")

    if missing:
        print("Components lacking coverage:")
        for issue in missing:
            print(f"- {issue}")
        sys.exit(1)

    print("All components have tests and documentation.")


if __name__ == "__main__":
    main()
