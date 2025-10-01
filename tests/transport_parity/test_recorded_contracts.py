"""Recorded REST↔gRPC/MCP parity contract tests using sandbox fixtures."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

import pytest

from . import FIXTURE_ROOT, STAGE_E_CONNECTORS

IGNORED_FIELDS: set[str] = {
    "transport",
    "recorded_at",
    "revision",
    "neo_revision",
    "neo_observer",
}
REQUIRED_ROTATION_PHASES: tuple[str, ...] = ("precheck", "handover", "stabilize")
ENVIRONMENTS: tuple[str, ...] = ("legacy", "neo")
CHANNELS: tuple[str, ...] = ("rest", "grpc")


@dataclass(frozen=True)
class ParitySuite:
    """Container describing a recorded parity suite."""

    name: str
    connector: str
    stage: str
    path: Path
    payload: Mapping[str, Any]


@lru_cache(maxsize=1)
def _load_parity_suites() -> tuple[ParitySuite, ...]:
    suites: list[ParitySuite] = []
    for path in sorted(FIXTURE_ROOT.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        suites.append(
            ParitySuite(
                name=path.stem,
                connector=data.get("connector", path.stem),
                stage=data.get("stage", ""),
                path=path,
                payload=data,
            )
        )
    if not suites:
        raise AssertionError("expected at least one recorded transport parity suite")
    return tuple(suites)


def _sanitize_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    canonical: dict[str, Any] = {}
    for key, value in mapping.items():
        if key in IGNORED_FIELDS:
            continue
        if key == "span_chain":
            if isinstance(value, list) and value:
                canonical["span_root"] = value[0]
            continue
        canonical[key] = value
    return canonical


def _canonical_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    canonical: dict[str, Any] = {}
    for environment in ENVIRONMENTS:
        channels = payload[environment]
        canonical[environment] = {
            channel: _sanitize_mapping(channels[channel]) for channel in CHANNELS
        }
    return canonical


def _canonical_telemetry(telemetry: Mapping[str, Any]) -> Mapping[str, Any]:
    return {env: _sanitize_mapping(telemetry[env]) for env in ENVIRONMENTS}


@pytest.fixture(scope="module")
def parity_suite_catalog() -> tuple[ParitySuite, ...]:
    return _load_parity_suites()


@pytest.fixture(params=_load_parity_suites(), ids=lambda suite: suite.connector)
def parity_suite(request: pytest.FixtureRequest) -> ParitySuite:
    return request.param


def _iter_mcp_phases(entries: Iterable[Mapping[str, Any]]) -> list[str]:
    return [str(entry.get("phase", "")) for entry in entries]


def _root_span(chain: Iterable[str] | None) -> str | None:
    if not chain:
        return None
    for item in chain:
        return item
    return None


def _assert_response_shapes(
    suite: ParitySuite, environment: str, rest: Mapping[str, Any], grpc: Mapping[str, Any]
) -> None:
    assert rest["command_id"] == grpc["command_id"], (
        f"{suite.connector} {environment} command id mismatch"
    )
    assert rest["status"] == grpc["status"], (
        f"{suite.connector} {environment} status mismatch"
    )
    assert rest["payload"] == grpc["payload"], (
        f"{suite.connector} {environment} payload mismatch"
    )
    rest_root = _root_span(rest.get("span_chain"))
    grpc_root = _root_span(grpc.get("span_chain"))
    assert rest_root and rest_root == grpc_root, (
        f"{suite.connector} {environment} span roots differ"
    )


def test_stage_e_catalog_covers_all_connectors(parity_suite_catalog: tuple[ParitySuite, ...]) -> None:
    connectors = {suite.connector for suite in parity_suite_catalog}
    missing = set(STAGE_E_CONNECTORS) - connectors
    assert not missing, f"missing parity fixtures: {sorted(missing)}"
    assert len(connectors) == len(parity_suite_catalog), "duplicate connector fixtures detected"


def test_stage_markers_align_with_stage_e(parity_suite_catalog: tuple[ParitySuite, ...]) -> None:
    for suite in parity_suite_catalog:
        assert suite.stage == "stage_e", f"unexpected stage marker in {suite.path}"


def test_rest_and_grpc_payloads_align_for_each_environment(parity_suite: ParitySuite) -> None:
    payloads = parity_suite.payload["responses"]
    for environment in ENVIRONMENTS:
        rest = payloads[environment]["rest"]
        grpc = payloads[environment]["grpc"]
        _assert_response_shapes(parity_suite, environment, rest, grpc)
        assert _sanitize_mapping(rest) == _sanitize_mapping(grpc)


def test_legacy_and_neo_contracts_match(parity_suite: ParitySuite) -> None:
    payloads = parity_suite.payload["responses"]
    legacy_rest = _sanitize_mapping(payloads["legacy"]["rest"])
    neo_rest = _sanitize_mapping(payloads["neo"]["rest"])
    legacy_grpc = _sanitize_mapping(payloads["legacy"]["grpc"])
    neo_grpc = _sanitize_mapping(payloads["neo"]["grpc"])
    assert legacy_rest == neo_rest, f"REST contract drift detected for {parity_suite.connector}"
    assert legacy_grpc == neo_grpc, f"gRPC contract drift detected for {parity_suite.connector}"


def test_telemetry_metrics_match(parity_suite: ParitySuite) -> None:
    telemetry = parity_suite.payload["telemetry"]
    legacy = telemetry["legacy"]
    neo = telemetry["neo"]
    comparable_fields = (
        "command_id",
        "latency_ms_p50",
        "latency_ms_p95",
        "latency_ms_p99",
        "error_rate",
        "fallback_invocations",
        "rotation_window",
        "mcp_lease",
    )
    for field in comparable_fields:
        assert legacy[field] == neo[field], (
            f"telemetry field {field} drift for {parity_suite.connector}"
        )
    assert _root_span(legacy.get("span_chain")) == _root_span(neo.get("span_chain")), (
        f"telemetry span roots differ for {parity_suite.connector}"
    )


def test_mcp_rotations_cover_required_phases(parity_suite: ParitySuite) -> None:
    rotations = parity_suite.payload["mcp_rotations"]
    for environment in ENVIRONMENTS:
        entries = rotations[environment]
        phases = _iter_mcp_phases(entries)
        assert tuple(phases) == REQUIRED_ROTATION_PHASES, (
            f"rotation phases mismatch for {parity_suite.connector} {environment}: {phases}"
        )
        statuses = {entry.get("status") for entry in entries}
        assert statuses == {"completed"}, (
            f"rotation status incomplete for {parity_suite.connector} {environment}: {statuses}"
        )


def test_recorded_checksum_matches_payload(parity_suite: ParitySuite) -> None:
    payload = parity_suite.payload
    canonical = {
        "connector": parity_suite.connector,
        "stage": parity_suite.stage,
        "responses": _canonical_payload(payload["responses"]),
        "telemetry": _canonical_telemetry(payload["telemetry"]),
    }
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode("utf-8")).hexdigest()
    recorded = payload["evidence"]["parity_checksum"]
    assert digest == recorded, (
        f"checksum mismatch for {parity_suite.connector}: {digest} != {recorded}"
    )


def test_evidence_paths_reference_stage_e_logs(parity_suite: ParitySuite) -> None:
    evidence = parity_suite.payload["evidence"]
    for key in ("diff_path", "telemetry_log", "mcp_rotation_log"):
        value = evidence.get(key)
        assert isinstance(value, str) and value, (
            f"missing evidence path {key} for {parity_suite.connector}"
        )
        assert "logs/stage_e" in value, (
            f"evidence path {value} does not reference Stage E snapshot"
        )

