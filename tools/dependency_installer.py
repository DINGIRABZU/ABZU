from __future__ import annotations

"""Install Python packages into a given virtual environment."""

from pathlib import Path
from typing import Sequence

from . import virtual_env_manager


def install_packages(env: Path, packages: Sequence[str]) -> None:
    """Install *packages* into the virtual environment at *env*.

    Parameters
    ----------
    env:
        Path to the virtual environment directory.
    packages:
        An iterable of package names to install.
    """
    if not packages:
        return
    virtual_env_manager.run(env, ["pip", "install", *packages])
