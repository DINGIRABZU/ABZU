"""Tests for the LWM configuration model."""

from __future__ import annotations

from pathlib import Path

from lwm.config_model import LWMConfig, load_config


def test_load_config(tmp_path: Path) -> None:
    cfg = tmp_path / "lwm.yaml"
    cfg.write_text(
        """
paths:
  model_dir: /models
  output_dir: /out
gpu:
  use_cuda: true
  device: 1
""",
        encoding="utf-8",
    )
    loaded = load_config(cfg)
    assert isinstance(loaded, LWMConfig)
    assert loaded.paths.model_dir == Path("/models")
    assert loaded.gpu.use_cuda is True
    assert loaded.gpu.device == 1
