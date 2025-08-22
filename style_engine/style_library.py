"""Utilities for loading video style configurations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

STYLES_DIR = Path(__file__).parent / "styles"


@dataclass
class StyleConfig:
    """Configuration describing a video style preset."""

    name: str
    processor: str


def load_style_config(name: str, styles_dir: Path | None = None) -> StyleConfig:
    """Load a style configuration by ``name`` from a YAML preset."""
    directory = styles_dir or STYLES_DIR
    path = directory / f"{name}.yaml"
    data = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    processor = data.get("processor", name)
    return StyleConfig(name=name, processor=processor)
