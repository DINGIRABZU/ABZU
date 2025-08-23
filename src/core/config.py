"""Utility functions for loading YAML configuration files."""

from __future__ import annotations

from pathlib import Path
from omegaconf import OmegaConf, DictConfig

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def load_config(name: str = "settings") -> DictConfig:
    """Load ``name`` from the :mod:`config` directory.

    Parameters
    ----------
    name:
        Base name of the YAML file without extension.
    """
    return OmegaConf.load(CONFIG_DIR / f"{name}.yaml")


__all__ = ["load_config"]
