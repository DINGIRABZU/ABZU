"""Configuration models for Spiral OS.

This module defines typed configuration objects and utilities for loading them
from the ``settings.yaml`` file. Validation is performed using Pydantic to
ensure runtime options are well‑formed.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, HttpUrl


class ServicesConfig(BaseModel):
    """Endpoints for external services used by the application."""

    animation_service_url: HttpUrl


class AudioConfig(BaseModel):
    """Audio processing parameters."""

    sample_rate: int = Field(default=44_100, gt=0)


class Config(BaseModel):
    """Top level configuration validated by Pydantic."""

    services: ServicesConfig
    audio: AudioConfig


def load_config(path: Path | None = None) -> Config:
    """Load configuration data from ``settings.yaml``.

    Parameters
    ----------
    path:
        Optional path to the configuration file. Defaults to ``settings.yaml``
        located in the same directory as this module.

    Returns
    -------
    Config
        Parsed and validated configuration object.
    """

    if path is None:
        path = Path(__file__).with_name("settings.yaml")

    data = yaml.safe_load(path.read_text())
    return Config(**data)


__all__ = ["Config", "load_config", "ServicesConfig", "AudioConfig"]

