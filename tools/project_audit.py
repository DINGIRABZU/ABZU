from __future__ import annotations

"""Simple project audit for Spiral OS."""

from pathlib import Path
import importlib
import sys
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
REQUIRED_MODULES = [
    "qnl_engine",
    "audio_engine",
    "vector_memory",
]


def _parse_missing_dep(error: ModuleNotFoundError) -> str:
    return error.name


def check_module(name: str) -> List[str]:
    """Return a list of warnings for the given module name."""
    warnings: List[str] = []
    module_path = PROJECT_ROOT / f"{name}.py"
    if not module_path.exists():
        warnings.append(f"{name}.py not found")
        return warnings
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as exc:  # missing dependency
        warnings.append(
            f"Missing dependency '{_parse_missing_dep(exc)}' required by {name}"
        )
    except Exception as exc:  # pragma: no cover - unexpected
        warnings.append(f"Failed to import {name}: {exc}")
    return warnings


def main() -> int:
    print("Project audit results:\n")
    all_warnings: List[str] = []
    for mod in REQUIRED_MODULES:
        all_warnings.extend(check_module(mod))
    if all_warnings:
        print("Warnings:")
        for w in all_warnings:
            print(f"- {w}")
        return 1
    print("All required modules are present.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
