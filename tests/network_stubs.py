from __future__ import annotations

import types


def make_dotenv_stub() -> types.ModuleType:
    """Return a stub for the ``dotenv`` module."""
    module = types.ModuleType("dotenv")
    module.load_dotenv = lambda: None
    return module


def make_hub_stub() -> types.ModuleType:
    """Return a stub for the ``huggingface_hub`` module."""
    module = types.ModuleType("huggingface_hub")
    module.calls: list[dict] = []
    module.should_fail = False

    def snapshot_download(**kwargs):
        module.calls.append(kwargs)
        if module.should_fail:
            raise RuntimeError("boom")

    module.snapshot_download = snapshot_download
    return module
