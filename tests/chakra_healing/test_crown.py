"""Tests for crown chakra healing agent."""

from __future__ import annotations

from tests.chakra_healing.common import run_agent_test
import agents.chakra_healing.crown_agent as agent


def test_crown_agent(monkeypatch, tmp_path):
    result, calls, log_path, qlog = run_agent_test(agent, monkeypatch, tmp_path)
    assert result is True
    assert calls and log_path.exists() and qlog.exists()
