"""Bootstrap the development environment."""

from __future__ import annotations

import importlib
import subprocess
import sys
import warnings
from pathlib import Path
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


def detect_device() -> str:
    """Detect available GPU acceleration and warn on CPU fallback."""
    try:
        import torch
    except Exception:  # pragma: no cover - torch may not be installed
        warnings.warn("PyTorch is not installed; defaulting to CPU")
        return "cpu"

    if torch.cuda.is_available():
        if getattr(torch.version, "hip", None):
            print("ROCm GPU detected")
            return "rocm"
        if getattr(torch.version, "cuda", None):
            print("CUDA GPU detected")
            return "cuda"
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        print("Intel GPU detected")
        return "xpu"

    warnings.warn("No supported GPU detected; using CPU")
    return "cpu"


def log_hardware_support(
    device: str, path: str | Path = "docs/hardware_support.md"
) -> None:
    """Record hardware probe results to a Markdown file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        rocm_available = bool(getattr(torch.version, "hip", None)) and cuda_available
        intel_available = hasattr(torch, "xpu") and torch.xpu.is_available()
    except Exception:  # pragma: no cover - torch may not be installed
        cuda_available = rocm_available = intel_available = False

    with path.open("w", encoding="utf-8") as f:
        f.write("# Hardware Support\n\n")
        f.write(f"- CUDA available: {cuda_available}\n")
        f.write(f"- ROCm available: {rocm_available}\n")
        f.write(f"- Intel GPU available: {intel_available}\n")
        f.write(f"- Selected device: {device}\n")


def main() -> None:
    """Run all bootstrap checks."""
    check_python()
    ensure_optional_deps()
    validate_env()
    device = detect_device()
    log_hardware_support(device)


if __name__ == "__main__":
    main()
