"""Tests for smoke imports."""


def test_import_src_and_agents():
    import src.core.config as core_config
    import agents.victim.security_canary as canary

    assert core_config is not None and canary is not None
