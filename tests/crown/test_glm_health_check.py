"""Tests for GLM health check during startup."""

from __future__ import annotations

import pytest

import init_crown_agent


class DummyIntegration:
    def __init__(self) -> None:
        self.called = False

    def health_check(self) -> None:
        self.called = True


def test_check_glm_invokes_health_check():
    integration = DummyIntegration()
    init_crown_agent._check_glm(integration)
    assert integration.called is True


def test_check_glm_failure():
    class FailingIntegration:
        def health_check(self) -> None:
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="GLM endpoint unavailable"):
        init_crown_agent._check_glm(FailingIntegration())
