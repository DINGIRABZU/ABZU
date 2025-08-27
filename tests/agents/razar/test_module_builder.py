from __future__ import annotations

from types import SimpleNamespace

import agents.razar.module_builder as module_builder


def _fake_remote(name: str, url: str, patch_context: str | None = None):
    suggestion = {
        "file": None,
        "content": "\n\ndef build():\n    return 'patched'\n",
    }
    return SimpleNamespace(__name__=name), {}, suggestion


def test_module_builder_creates_module(monkeypatch):
    monkeypatch.setattr(module_builder.remote_loader, "load_remote_agent", _fake_remote)

    spec = {
        "component": "agents/razar/generated_component.py",
        "tests": {
            "tests/test_generated_component.py": (
                "from agents.razar import generated_component\n"
                "def test_build():\n"
                "    assert generated_component.build() == 'patched'\n"
            )
        },
    }
    plan = {"generated_component": spec}

    path = module_builder.build(
        "generated_component", plan=plan, remote_agents=[("fake", "http://example.com")]
    )

    try:
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "TODO" in text
        assert "patched" in text
    finally:
        path.unlink(missing_ok=True)
