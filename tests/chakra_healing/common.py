"""Test helpers for chakra healing agents."""

from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
from typing import Tuple, List

from agents.chakra_healing import base


def run_agent_test(
    agent, monkeypatch, tmp_path: Path
) -> Tuple[bool, List[list[str]], Path, Path]:
    """Run ``agent.heal_if_needed`` with mocked dependencies."""

    def fake_get(url: str, timeout: int = 5) -> object:
        class DummyResp:
            def raise_for_status(self) -> None:  # pragma: no cover - trivial
                return None

            def json(self) -> dict[str, float]:
                return {"chakra": agent.CHAKRA, "value": agent.THRESHOLD + 1}

        return DummyResp()

    monkeypatch.setattr(base, "requests", SimpleNamespace(get=fake_get))

    calls: List[list[str]] = []

    def fake_run(cmd: list[str], check: bool = True) -> None:
        calls.append(cmd)

    monkeypatch.setattr(base.subprocess, "run", fake_run)

    base.LOG_PATH = tmp_path / "chakra.log"
    base.QUARANTINE_LOG = tmp_path / "quarantine.md"

    result = agent.heal_if_needed()
    return result, calls, base.LOG_PATH, base.QUARANTINE_LOG


__all__ = ["run_agent_test"]
