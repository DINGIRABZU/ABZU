"""Bootstrap the development environment."""

from __future__ import annotations

import importlib
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Dict

from _stage_runtime import (
    EnvironmentLimitedWarning,
    bootstrap,
    format_sandbox_summary,
)

ROOT = bootstrap(optional_modules=["env_validation"])

try:  # pragma: no cover - guarded import for sandboxed envs
    from env_validation import check_required
except Exception:  # pragma: no cover - fallback to stubbed check

    def check_required(_: tuple[str, ...]) -> None:
        warnings.warn(
            "environment-limited: env_validation unavailable; skipping checks",
            EnvironmentLimitedWarning,
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
                    EnvironmentLimitedWarning,
                    stacklevel=2,
                )


def validate_env() -> None:
    """Check that required environment variables are present."""
    try:
        check_required(REQUIRED_VARS)
    except SystemExit as exc:  # pragma: no cover - sandbox fallback
        warnings.warn(
            f"environment-limited: {exc}; continuing without required credentials",
            EnvironmentLimitedWarning,
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


HARDWARE_PROFILE_HEADER = """# Hardware Support

## Stage A Runner Profile

| Component | Specification |
| --- | --- |
| Chassis | Supermicro SYS-510P-ML with redundant 750 W PSUs |
| CPU | Intel Xeon Silver 4410Y (12 cores / 24 threads, 2.0 GHz base, 3.5 GHz turbo) |
| Memory | 128 GB DDR5-4800 ECC (4 × 32 GB) |
| Storage | 2 × 1 TB NVMe (RAID1) for OS, 1 × 2 TB NVMe scratch volume |
| Networking | Dual-port 10 GbE (SFP+) uplinks with bonded LACP |
| Accelerator | None (Stage A runs in CPU-only mode) |
"""


HARDWARE_PROFILE_GUIDANCE = """## Required Firmware and BIOS Settings

- BIOS version 2.5c with microcode package `14.0.45`.
- Enable `VT-d`, `SR-IOV`, and `Turbo Boost` while keeping `C-States` on `Auto` to
  reduce boot jitter.
- Update the BMC to 01.14.12 for correct power telemetry streaming into the
  Node Exporter panels.
- Stage A runners boot from UEFI with Secure Boot disabled to allow the
  telemetry sidecar to attach early in the initramfs.

## Exporter Configuration

- Install `node_exporter` with the textfile collector pointed at
  `/var/lib/node_exporter/textfile_collector/` and grant the CI user write
  access.
- Symlink `monitoring/boot_metrics.prom` into the collector directory after each
  gate run so Prometheus scrapes the first-attempt success, retry totals, and
  boot duration gauges.
- Add the following scrape job to `prometheus.yml` on the runner:

  ```yaml
  - job_name: "stage-a-boot-metrics"
    static_configs:
      - targets: ["localhost:9100"]
        labels:
          runner: "stage-a"
    params:
      collect[]:
        - textfile
  ```

- Include `monitoring/grafana-dashboard.json` in the Grafana provisioning
  config so the Boot Ops board automatically surfaces the new gauges alongside
  the Alpha gate summaries.
"""


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

    runtime_flags = (
        f"- CUDA available: {cuda_available}",
        f"- ROCm available: {rocm_available}",
        f"- Intel GPU available: {intel_available}",
        f"- Selected device: {device}",
    )

    with path.open("w", encoding="utf-8") as handle:
        handle.write(HARDWARE_PROFILE_HEADER)
        handle.write("\n### Runtime Flags\n\n")
        handle.write("\n".join(runtime_flags))
        handle.write("\n\n")
        handle.write(HARDWARE_PROFILE_GUIDANCE)


def main() -> None:
    """Run all bootstrap checks."""
    check_python()
    ensure_optional_deps()
    validate_env()
    device = detect_device()
    log_hardware_support(device)
    print(format_sandbox_summary("Stage A1 bootstrap completed"))


if __name__ == "__main__":
    main()
