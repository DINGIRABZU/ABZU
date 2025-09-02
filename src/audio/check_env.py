"""Diagnostic CLI to verify audio dependencies are installed."""

from __future__ import annotations

import importlib
import sys
from typing import Dict, Tuple

REQUIRED_PACKAGES: Dict[str, str] = {
    "librosa": "librosa",
    "soundfile": "soundfile",
    "opensmile": "opensmile",
    "clap": "clap",
    "rave": "rave",
}


def check_packages() -> Dict[str, Tuple[bool, str]]:
    """Attempt to import each required package and return status information."""
    results: Dict[str, Tuple[bool, str]] = {}
    for name, module_name in REQUIRED_PACKAGES.items():
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "unknown")
            results[name] = (True, str(version))
        except Exception as exc:  # pragma: no cover - diagnostic output
            results[name] = (False, str(exc))
    return results


def main() -> None:
    """Print the installation status of required audio packages."""
    results = check_packages()
    all_present = True
    for name, (ok, info) in results.items():
        if ok:
            print(f"{name}: {info}")
        else:
            all_present = False
            print(f"{name}: MISSING ({info})")
    sys.exit(0 if all_present else 1)


if __name__ == "__main__":
    main()
