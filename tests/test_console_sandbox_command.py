"""Tests for /sandbox command in console interface."""

from __future__ import annotations

import logging
import subprocess
import types

from cli import console_interface


class DummySession:
    def __init__(self, prompts: list[str]):
        self._prompts = prompts

    def prompt(self, _prompt: str) -> str:
        if not self._prompts:
            raise EOFError
        return self._prompts.pop(0)


class DummyContext:
    def __enter__(self) -> "DummyContext":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - no cleanup
        return False


def _setup(monkeypatch, tmp_path, run_behavior):
    patch_file = tmp_path / "change.diff"
    patch_file.write_text("patch-data")

    sandbox_root = tmp_path / "sandbox"
    calls: dict[str, object] = {}

    def fake_create(repo_root, env_manager):
        calls["create"] = True
        return sandbox_root

    def fake_apply(root, patch_text):
        calls["apply"] = patch_text

    def fake_install(env, req):
        calls["install"] = (env, req)

    def fake_run(env, cmd, cwd=None, **kwargs):
        calls["run"] = (env, cmd, cwd)
        if isinstance(run_behavior, Exception):
            raise run_behavior
        return run_behavior

    monkeypatch.setattr(console_interface, "_wait_for_glm_ready", lambda: object())
    monkeypatch.setattr(console_interface, "MoGEOrchestrator", lambda: object())
    monkeypatch.setattr(
        console_interface,
        "sandbox_session",
        types.SimpleNamespace(create_sandbox=fake_create, apply_patch=fake_apply),
    )
    monkeypatch.setattr(
        console_interface,
        "virtual_env_manager",
        types.SimpleNamespace(install_requirements=fake_install, run=fake_run),
    )
    monkeypatch.setattr(
        console_interface,
        "PromptSession",
        lambda history=None: DummySession([f"/sandbox {patch_file}", "/exit"]),
    )
    monkeypatch.setattr(console_interface, "patch_stdout", lambda: DummyContext())
    monkeypatch.setattr(console_interface, "FileHistory", lambda *a, **k: None)
    return calls


def test_sandbox_command_success(monkeypatch, tmp_path, capsys):
    run_result = types.SimpleNamespace(stdout="ok")
    calls = _setup(monkeypatch, tmp_path, run_result)
    console_interface.run_repl([])
    out = capsys.readouterr().out
    assert "Sandbox tests passed." in out
    assert calls["create"] is True
    assert calls["apply"] == "patch-data"
    assert calls["run"][1][0] == "pytest"
    env, req = calls["install"]
    assert env == tmp_path / "sandbox" / ".venv"
    assert req == tmp_path / "sandbox" / "tests" / "requirements.txt"


def test_sandbox_command_failure(monkeypatch, tmp_path, caplog):
    err = subprocess.CalledProcessError(1, ["pytest"], output="bad", stderr="fails")
    calls = _setup(monkeypatch, tmp_path, err)
    with caplog.at_level(logging.ERROR):
        console_interface.run_repl([])
    assert "Sandbox tests failed." in caplog.text
    assert calls["create"] is True
    assert calls["apply"] == "patch-data"
    assert calls["run"][1][0] == "pytest"
