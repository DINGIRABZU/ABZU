"""Validated configuration loading using Pydantic."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, HttpUrl


CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


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


def load_config(name: str = "settings") -> Config:
    """Load and validate ``name`` from the :mod:`config` directory."""

    data = yaml.safe_load((CONFIG_DIR / f"{name}.yaml").read_text())
    return Config(**data)


__all__ = ["Config", "load_config", "ServicesConfig", "AudioConfig"]

