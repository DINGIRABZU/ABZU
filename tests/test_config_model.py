"""Tests for the configuration model."""

from __future__ import annotations

from core.config import Config, load_config


def test_load_config() -> None:
    """Loading the default settings yields a validated ``Config`` object."""

    cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.audio.sample_rate == 44100

