"""Tests for orchestration master optional agents."""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import orchestration_master as om
from src.core.utils.seed import seed_all


def test_launch_agents_missing_optional(tmp_path):
    cfg = tmp_path / "agents.yaml"
    cfg.write_text(
        """
        bana:
          enabled: true
        asiangen:
          enabled: true
        landgraph:
          enabled: true
        """
    )

    called = {}
    bana_mod = types.ModuleType("agents.bana")
    bana_mod.launch = lambda: called.setdefault("bana", True)
    sys.modules["agents.bana"] = bana_mod

    seed_all(1)
    launched = om.launch_agents_from_config(cfg)
    assert launched == {"bana": True}
    assert called.get("bana") is True
