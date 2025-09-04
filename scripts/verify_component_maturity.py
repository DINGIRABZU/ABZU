#!/usr/bin/env python3
"""Verify component status versions and maturity requirements.

- Ensures versions listed in ``docs/component_status.json`` match the
  ``__version__`` values defined in code modules.
- Validates that modules marked Alpha or Beta in
  ``docs/chakra_architecture.md`` have associated documentation and tests.

Exit code is non-zero when any discrepancy is found.
"""
from __future__ import annotations

import json
import os
import re
import sys
from glob import glob
from typing import Dict, Iterable, List

ROOT = os.path.dirname(os.path.dirname(__file__))
STATUS_JSON = os.path.join(ROOT, "docs", "component_status.json")
CHAKRA_DOC = os.path.join(ROOT, "docs", "chakra_architecture.md")


def load_component_status() -> Dict[str, Dict[str, str]]:
    with open(STATUS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("components", {})


def get_file_version(path: str) -> str | None:
    pattern = re.compile(r"__version__\s*=\s*[\"']([^\"']+)[\"']")
    try:
        with open(os.path.join(ROOT, path), "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    return match.group(1)
    except FileNotFoundError:
        return None
    return None


def parse_chakra_components() -> Iterable[str]:
    with open(CHAKRA_DOC, "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.strip().split("|")[1:-1]]
            if len(parts) < 4:
                continue
            component_col, quality = parts[1], parts[3]
            if quality not in {"Alpha", "Beta"}:
                continue
            for comp in component_col.split(","):
                comp = comp.strip().strip("`")
                if comp.endswith((".py", "/")):
                    yield comp.rstrip("/")


def has_docs(component: str) -> bool:
    name = os.path.basename(component)
    for doc in glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True):
        with open(doc, "r", encoding="utf-8") as f:
            text = f.read()
            if component in text or name in text:
                return True
    return False


def has_tests(component: str) -> bool:
    base = os.path.basename(component).split(".")[0]
    import_path = component.replace("/", ".").rstrip(".py")
    for test in glob(os.path.join(ROOT, "tests", "**", "*.py"), recursive=True):
        with open(test, "r", encoding="utf-8") as f:
            text = f.read()
            if base in text or import_path in text:
                return True
    return False


def main() -> int:
    status = load_component_status()
    tracked = [c for c in parse_chakra_components() if c in status]
    mismatched: List[str] = []
    for path in tracked:
        info = status[path]
        if not path.endswith(".py"):
            continue
        expected = info.get("version")
        actual = get_file_version(path)
        if actual and expected and actual != expected:
            mismatched.append(f"{path}: expected {expected}, found {actual}")

    missing_docs: List[str] = []
    missing_tests: List[str] = []
    for comp in parse_chakra_components():
        if not has_docs(comp):
            missing_docs.append(comp)
        if not has_tests(comp):
            missing_tests.append(comp)

    if mismatched:
        print("Version mismatches detected:")
        for line in mismatched:
            print(f" - {line}")
    if missing_docs:
        print("Missing documentation for:")
        for comp in missing_docs:
            print(f" - {comp}")
    if missing_tests:
        print("Missing tests for:")
        for comp in missing_tests:
            print(f" - {comp}")

    if mismatched or missing_docs or missing_tests:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
