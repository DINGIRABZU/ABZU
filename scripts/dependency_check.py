"""Verify package imports and optional dependencies.

from __future__ import annotations

Run from the repository root:

    python scripts/dependency_check.py

The script executes ``pip check`` to validate installed packages, attempts to
import core components and simulates missing optional dependencies. Each
component receives a score out of 10 with deductions applied for absent
optional modules. Severity levels are logged for quick triage.
"""

import importlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


@dataclass
class OptionalDep:
    name: str
    severity: str
    deduction: int


# Component configuration with optional dependency metadata
COMPONENTS = {
    "vector_memory": {
        "module": "vector_memory",
        "optional": [OptionalDep("faiss", "high", 3)],
    },
    "rag": {
        "module": "rag",
        "optional": [OptionalDep("omegaconf", "medium", 2)],
    },
    "spiral_os": {"module": "SPIRAL_OS", "optional": []},
    "INANNA_AI": {"module": "INANNA_AI", "optional": []},
}


def run_pip_check() -> tuple[bool, str]:
    """Run ``pip check`` and return success flag and combined output."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "check",
        ],
        capture_output=True,
        text=True,
    )
    output = proc.stdout.strip() or proc.stderr.strip()
    return proc.returncode == 0, output


def evaluate_components() -> dict[str, dict]:
    """Import components and assess optional dependency availability.

    Returns a mapping of component label to a dictionary containing:

    ``ok``: Whether the component imported successfully.
    ``missing``: List of tuples ``(dependency, severity)`` for each absent
        optional dependency.
    ``score``: Final score after deductions for missing optional dependencies.
    """

    results: dict[str, dict] = {}
    for label, data in COMPONENTS.items():
        module = data["module"]
        optional = data.get("optional", [])

        try:
            importlib.import_module(module)
            ok = True
        except Exception:  # pragma: no cover - import error handled
            ok = False

        score = 10 if ok else 0
        missing: list[tuple[str, str]] = []

        if ok:
            for dep in optional:
                try:
                    importlib.import_module(dep.name)
                except Exception:  # pragma: no cover - import error handled
                    missing.append((dep.name, dep.severity))
                    score -= dep.deduction

        results[label] = {
            "ok": ok,
            "missing": missing,
            "score": max(score, 0),
        }

    return results


def main() -> None:
    pip_ok, pip_output = run_pip_check()
    comp_results = evaluate_components()

    print("pip check:", "passed" if pip_ok else "failed")
    if pip_output:
        print(pip_output)

    print("\nComponent status:")
    for name, data in comp_results.items():
        if data["ok"] and not data["missing"]:
            icon = "✅"
            extra = f" score={data['score']}"
        elif data["ok"]:
            icon = "⚠️"
            miss = ", ".join(f"{dep} ({sev})" for dep, sev in data["missing"])
            extra = f" score={data['score']} - missing {miss}"
        else:
            icon = "❌"
            extra = " - import failed score=0"
        print(f"- {name}: {icon}{extra}")

    # Aggregate list of missing optional modules for summary
    all_missing = sorted(
        {dep for v in comp_results.values() for dep, _ in v["missing"]}
    )
    if all_missing:
        print("\nMissing optional modules:", ", ".join(all_missing))


if __name__ == "__main__":
    main()
