"""Bootstrap the development environment."""

from __future__ import annotations

import importlib
import subprocess
import sys
from typing import Dict

from env_validation import check_required

REQUIRED_VARS = ("HF_TOKEN", "GITHUB_TOKEN", "OPENAI_API_KEY")
OPTIONAL_DEPS: Dict[str, str] = {
    "faiss": "faiss-cpu",
    "sqlite3": "pysqlite3-binary",
}


def check_python() -> None:
    """Ensure the running Python meets the minimum version."""
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or higher is required")


def install(package: str) -> None:
    """Install a package using ``pip``."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def ensure_optional_deps() -> None:
    """Install optional dependencies if they are missing."""
    for module, package in OPTIONAL_DEPS.items():
        try:
            importlib.import_module(module)
        except Exception:  # pragma: no cover - import errors vary
            install(package)


def validate_env() -> None:
    """Check that required environment variables are present."""
    check_required(REQUIRED_VARS)


def main() -> None:
    """Run all bootstrap checks."""
    check_python()
    ensure_optional_deps()
    validate_env()


if __name__ == "__main__":
    main()
