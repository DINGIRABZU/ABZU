from __future__ import annotations

"""Environment builder for RAZAR.

This module verifies that a suitable Python interpreter is available,
creates an isolated virtual environment and installs dependencies for
each component layer defined in a configuration file.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
import venv

try:
    import yaml
except ImportError as exc:  # pragma: no cover - handled in tests
    raise RuntimeError("pyyaml is required to load environment configuration") from exc

LOGGER = logging.getLogger("razar.environment_builder")


def ensure_python(version: str) -> None:
    """Ensure ``version`` of Python is available.

    The builder relies on ``pyenv`` for installation if the requested version
    does not match the current interpreter. If ``pyenv`` is not present an
    informative error is raised.
    """

    current = f"{sys.version_info.major}.{sys.version_info.minor}"
    if current.startswith(version):
        LOGGER.info("Using system Python %s", current)
        return

    LOGGER.info("Installing Python %s via pyenv", version)
    try:
        subprocess.run(["pyenv", "install", "-s", version], check=True)
    except Exception as exc:  # pragma: no cover - depends on host
        raise RuntimeError(
            f"Python {version} required but pyenv installation failed"
        ) from exc


def create_virtualenv(path: Path) -> None:
    """Create a virtual environment at ``path`` if missing."""

    if path.exists():
        LOGGER.info("Using existing virtual environment at %s", path)
        return

    LOGGER.info("Creating virtual environment at %s", path)
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(path)


def _pip_executable(venv_path: Path) -> Path:
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    return venv_path / bin_dir / "pip"


def install_packages(venv_path: Path, packages: list[str]) -> None:
    """Install ``packages`` into the virtual environment located at ``venv_path``."""

    if not packages:
        return
    pip = _pip_executable(venv_path)
    cmd = [str(pip), "install", "--disable-pip-version-check", *packages]
    LOGGER.info("Installing packages: %s", ", ".join(packages))
    subprocess.run(cmd, check=True)


def read_layers(config_path: Path) -> dict[str, list[str]]:
    """Return mapping of layer name to package list from ``config_path``."""

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw_layers = data.get("layers") or {}
    layers: dict[str, list[str]] = {}
    for name, packages in raw_layers.items():
        layers[name] = list(packages or [])
    return layers


def install_layers(config_path: Path, venv_path: Path) -> None:
    """Install dependencies for each layer defined in ``config_path``."""

    for name, packages in read_layers(config_path).items():
        LOGGER.info("\n--- Installing layer: %s ---", name)
        install_packages(venv_path, packages)


def main() -> None:  # pragma: no cover - CLI helper
    parser = argparse.ArgumentParser(description="Build RAZAR environment")
    default_cfg = Path(__file__).resolve().parent.parent / "razar_env.yaml"
    parser.add_argument(
        "--config",
        type=Path,
        default=default_cfg,
        help="Path to razar_env.yaml",
    )
    parser.add_argument(
        "--python",
        default=f"{sys.version_info.major}.{sys.version_info.minor}",
        help="Python version to ensure",
    )
    parser.add_argument(
        "--venv",
        type=Path,
        default=Path(".razar_venv"),
        help="Location for virtual environment",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    ensure_python(str(args.python))
    create_virtualenv(args.venv)
    install_layers(args.config, args.venv)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

