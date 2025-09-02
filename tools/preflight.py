"""Run basic environment validation in a single command."""

from __future__ import annotations

__version__ = "0.1.0"

import argparse
import importlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env_validation import (
    check_optional_packages,
    check_required,
    check_required_binaries,
)

REQUIRED_ENV_VARS = ["HF_TOKEN", "GLM_API_URL"]
OPTIONAL_PACKAGES = ["numpy", "torch"]
REQUIRED_BINARIES = ["ffmpeg", "sox"]


def _check_optional_packages(packages: list[str]) -> list[str]:
    missing = []
    for name in packages:
        try:
            importlib.import_module(name)
        except Exception:
            missing.append(name)
    check_optional_packages(packages)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate environment variables, packages and binaries."
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Emit a JSON summary of detected issues and recommended fixes.",
    )
    args = parser.parse_args()

    report: dict[str, list[dict[str, str]]] = {
        "env": [],
        "packages": [],
        "binaries": [],
    }

    try:
        check_required(REQUIRED_ENV_VARS)
    except SystemExit as exc:
        missing = str(exc).split(": ", 1)[1].split(", ")
        report["env"] = [
            {"name": n, "fix": f"Set {n} in the environment"} for n in missing
        ]

    missing_packages = _check_optional_packages(OPTIONAL_PACKAGES)
    if missing_packages:
        report["packages"] = [
            {"name": n, "fix": f"pip install {n}"} for n in missing_packages
        ]

    try:
        check_required_binaries(REQUIRED_BINARIES)
    except SystemExit as exc:
        missing = str(exc).split(": ", 1)[1].split(", ")
        report["binaries"] = [
            {
                "name": n,
                "fix": f"Install {n} using your system package manager",
            }
            for n in missing
        ]

    if args.report:
        print(json.dumps(report, indent=2))
    else:
        if any(report.values()):
            print("Preflight checks found issues:")
            for category in ["env", "packages", "binaries"]:
                for item in report[category]:
                    print(f"- {item['name']}: {item['fix']}")
        else:
            print("All preflight checks passed.")

    return 0 if not any(report.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
