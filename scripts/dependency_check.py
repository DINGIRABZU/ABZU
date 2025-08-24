from __future__ import annotations

"""Verify package imports and optional dependencies.

Run from the repository root:

    python scripts/dependency_check.py

The script executes ``pip check`` to validate installed packages, attempts to
import core components and reports missing optional modules such as FAISS or
OmegaConf.
"""

import importlib
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Mapping of label -> module import path
COMPONENTS = {
    "vector_memory": "vector_memory",
    "rag": "rag",
    "spiral_os": "SPIRAL_OS",  # package name used for import
    "INANNA_AI": "INANNA_AI",
}

# Optional third-party dependencies
OPTIONAL_DEPS = ["faiss", "omegaconf"]


def run_pip_check() -> tuple[bool, str]:
    """Run ``pip check`` and return success flag and combined output."""
    proc = subprocess.run([
        sys.executable,
        "-m",
        "pip",
        "check",
    ], capture_output=True, text=True)
    output = proc.stdout.strip() or proc.stderr.strip()
    return proc.returncode == 0, output


def check_components() -> dict[str, bool]:
    """Attempt to import each component and return success flags."""
    results: dict[str, bool] = {}
    for label, module in COMPONENTS.items():
        try:
            importlib.import_module(module)
        except Exception:  # pragma: no cover - import error handled
            results[label] = False
        else:
            results[label] = True
    return results


def missing_optional() -> list[str]:
    """Return a list of optional modules that are not installed."""
    missing: list[str] = []
    for name in OPTIONAL_DEPS:
        try:
            importlib.import_module(name)
        except Exception:  # pragma: no cover - import error handled
            missing.append(name)
    return missing


def main() -> None:
    pip_ok, pip_output = run_pip_check()
    comp_results = check_components()
    optional_missing = missing_optional()

    print("pip check:", "passed" if pip_ok else "failed")
    if pip_output:
        print(pip_output)

    print("\nComponent status:")
    for name, ok in comp_results.items():
        if ok and not optional_missing:
            icon, extra = "✅", ""
        elif ok:
            icon, extra = "⚠️", " - optional deps missing"
        else:
            icon, extra = "❌", " - import failed"
        print(f"- {name}: {icon}{extra}")

    if optional_missing:
        print("\nMissing optional modules:", ", ".join(optional_missing))


if __name__ == "__main__":
    main()

