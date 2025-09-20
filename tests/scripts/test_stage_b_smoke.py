import asyncio
import importlib.util
import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path

from tests.conftest import allow_test

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "connectors" / "operator_mcp_adapter.py"
SPEC = importlib.util.spec_from_file_location(
    "connectors.operator_mcp_adapter", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
adapter_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter_module)  # type: ignore[misc]

connectors_stub = ModuleType("connectors")
connectors_stub.__path__ = [str(MODULE_PATH.parent)]
connectors_stub.operator_mcp_adapter = adapter_module
sys.modules["connectors"] = connectors_stub
sys.modules["connectors.operator_mcp_adapter"] = adapter_module

allow_test(__file__)

from scripts import stage_b_smoke


def test_run_stage_b_smoke_invokes_rotation(monkeypatch):
    handshake_payload = {
        "session": {"id": "sess"},
        "accepted_contexts": ["stage-b-rehearsal"],
    }
    heartbeat_calls: list[SimpleNamespace] = []

    class DummyAdapter:
        def __init__(self) -> None:
            self.handshake_count = 0

        async def ensure_handshake(self) -> dict[str, object]:
            self.handshake_count += 1
            return handshake_payload

        async def emit_stage_b_heartbeat(self, payload, credential_expiry=None):
            heartbeat_calls.append(
                SimpleNamespace(payload=payload, credential_expiry=credential_expiry)
            )
            return payload

    rotations: list[str] = []

    monkeypatch.setattr(stage_b_smoke, "OperatorMCPAdapter", DummyAdapter)
    monkeypatch.setattr(stage_b_smoke, "stage_b_context_enabled", lambda: True)
    monkeypatch.setattr(stage_b_smoke, "record_rotation_drill", rotations.append)
    monkeypatch.setattr(stage_b_smoke, "evaluate_operator_doctrine", lambda: (True, []))
    monkeypatch.setattr(
        stage_b_smoke,
        "_collect_crown_metadata",
        lambda: {"version": "0.0", "module": "stub"},
    )

    results = asyncio.run(stage_b_smoke.run_stage_b_smoke())
    assert (
        results["services"]["operator_api"]["session"] == handshake_payload["session"]
    )
    assert rotations == ["operator_api", "operator_upload"]
    assert heartbeat_calls, "Heartbeat emission should be triggered"


def test_main_invokes_async_runner(monkeypatch):
    captured_args = {}

    async def fake_async_main(args):
        captured_args["args"] = args
        return 0

    monkeypatch.setattr(stage_b_smoke, "_async_main", fake_async_main)
    exit_code = stage_b_smoke.main(["--json", "--skip-heartbeat"])
    assert exit_code == 0
    assert captured_args["args"].json is True
    assert captured_args["args"].skip_heartbeat is True
