"""Bootstrap the development environment."""

from __future__ import annotations

import importlib
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Dict

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from scripts import _stage_runtime

ROOT = _stage_runtime.bootstrap(optional_modules=["env_validation"])

try:  # pragma: no cover - guarded import for sandboxed envs
    from env_validation import check_required
except Exception:  # pragma: no cover - fallback to stubbed check

    def check_required(_: tuple[str, ...]) -> None:
        warnings.warn(
            "environment-limited: env_validation unavailable; skipping checks",
            _stage_runtime.EnvironmentLimitedWarning,
            stacklevel=2,
        )


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
            try:
                install(package)
            except subprocess.CalledProcessError as exc:
                warnings.warn(
                    (
                        "environment-limited: unable to install optional package "
                        f"'{package}' ({exc})"
                    ),
                    _stage_runtime.EnvironmentLimitedWarning,
                    stacklevel=2,
                )


def validate_env() -> None:
    """Check that required environment variables are present."""
    try:
        check_required(REQUIRED_VARS)
    except SystemExit as exc:  # pragma: no cover - sandbox fallback
        warnings.warn(
            f"environment-limited: {exc}; continuing without required credentials",
            _stage_runtime.EnvironmentLimitedWarning,
            stacklevel=2,
        )


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
    device: str, path: str | Path = ROOT / "docs/hardware_support.md"
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
    print(_stage_runtime.format_sandbox_summary("Stage A1 bootstrap completed"))


if __name__ == "__main__":
    main()
