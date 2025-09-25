from __future__ import annotations

import json
import importlib
from types import SimpleNamespace

from scripts.check_memory_layers import MemoryLayerCheckReport, OptionalStubActivation


def _create_dataset(path, queries) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for query in queries:
            handle.write(json.dumps({"query": query}))
            handle.write("\n")


def test_run_load_proof_stubbed_metadata_and_log(tmp_path):
    module = importlib.import_module("scripts.memory_load_proof")
    dataset = tmp_path / "fixture.jsonl"
    _create_dataset(dataset, ["alpha", "beta", "gamma", "delta"])

    args = SimpleNamespace(
        dataset=dataset,
        query_field="query",
        limit=None,
        warmup=0,
        metrics_source="test",
        metrics_output=None,
    )

    result = module.run_load_proof(args)

    assert result.stubbed is True
    assert result.implementation.endswith("neoabzu_stub")

    log_path = tmp_path / "run.log"
    module._append_log(result, log_path)
    with log_path.open("r", encoding="utf-8") as handle:
        payload = json.loads(handle.readline())
    assert payload["bundle_implementation"].endswith("neoabzu_stub")
    assert payload["stubbed_bundle"] is True


class _FakeNativeBundle:
    def __init__(self) -> None:
        self.stubbed = False
        self.fallback_reason = None
        self.implementation = "neoabzu_memory"
        self._initialized = False

    def initialize(self) -> dict[str, object]:
        statuses = {
            "cortex": "ready",
            "vector": "ready",
            "spiral": "ready",
            "emotional": "ready",
            "mental": "ready",
            "spiritual": "ready",
            "narrative": "ready",
            "core": "ready",
        }
        diagnostics = {
            layer: {"status": "ready", "loaded_module": "neoabzu_memory"}
            for layer in statuses
        }
        diagnostics["__bundle__"] = {
            "implementation": self.implementation,
            "stubbed": False,
            "source_module": "neoabzu_memory",
        }
        self._initialized = True
        return {
            "statuses": statuses,
            "diagnostics": diagnostics,
            "stubbed": False,
            "implementation": self.implementation,
        }

    def query(self, text: str) -> dict[str, object]:
        if not self._initialized:
            raise RuntimeError("Bundle not initialized")
        return {"failed_layers": [], "core": "native"}


def test_run_load_proof_native_metadata(monkeypatch, tmp_path):
    module = importlib.reload(importlib.import_module("scripts.memory_load_proof"))
    monkeypatch.setattr(module, "MemoryBundle", _FakeNativeBundle)

    dataset = tmp_path / "fixture.jsonl"
    _create_dataset(dataset, ["alpha", "beta", "gamma"])

    args = SimpleNamespace(
        dataset=dataset,
        query_field="query",
        limit=None,
        warmup=0,
        metrics_source="test",
        metrics_output=None,
    )

    result = module.run_load_proof(args)

    assert result.stubbed is False
    assert result.implementation == "neoabzu_memory"
    assert result.fallback_reason is None


def test_append_pretest_report_includes_implementation(tmp_path):
    module = importlib.import_module("scripts.memory_load_proof")
    report = MemoryLayerCheckReport(
        statuses={"cortex": "ready"},
        optional_stubs=[
            OptionalStubActivation(
                layer="cortex",
                module="memory.optional.neoabzu_stub",
                reason="test",
            )
        ],
        bundle_implementation="memory.optional.neoabzu_stub",
    )

    log_path = tmp_path / "pretest.log"
    module._append_pretest_report(
        report, tmp_path / "dataset.jsonl", log_path, stubbed=True
    )

    with log_path.open("r", encoding="utf-8") as handle:
        payload = json.loads(handle.readline())

    assert payload["bundle_implementation"] == "memory.optional.neoabzu_stub"
    assert payload["stubbed_bundle"] is True
