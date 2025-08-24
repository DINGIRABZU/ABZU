"""Configuration model for the Large World Model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from omegaconf import OmegaConf


@dataclass
class GPUConfig:
    """GPU flags controlling CUDA usage."""

    use_cuda: bool = False
    device: int = 0


@dataclass
class PathConfig:
    """Filesystem paths used by the Large World Model."""

    model_dir: Path = Path("models/lwm")
    output_dir: Path = Path("outputs/lwm")


@dataclass
class LWMConfig:
    """Aggregate configuration for the Large World Model."""

    paths: PathConfig = field(default_factory=PathConfig)
    gpu: GPUConfig = field(default_factory=GPUConfig)


def load_config(config_path: str | Path = Path("config/lwm.yaml")) -> LWMConfig:
    """Load an ``LWMConfig`` from ``config_path``.

    Parameters
    ----------
    config_path:
        Location of the YAML configuration file.
    """
    data = cast(
        dict[str, Any],
        OmegaConf.to_container(OmegaConf.load(config_path), resolve=True),
    )
    path_conf = {k: Path(v) for k, v in data.get("paths", {}).items()}
    gpu_conf = data.get("gpu", {})
    return LWMConfig(paths=PathConfig(**path_conf), gpu=GPUConfig(**gpu_conf))
