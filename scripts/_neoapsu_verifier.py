"""Shared helpers for Neo-APSU Stage D verification CLIs."""

from __future__ import annotations

import importlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

LOGGER = logging.getLogger(__name__)


def _stringify_value(value: Any) -> Any:
    """Return ``value`` coerced into JSON-serialisable primitives."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _stringify_value(val) for key, val in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_stringify_value(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def load_migration_entries(
    matrix_path: Path, match_tokens: Sequence[str]
) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]], list[str]]:
    """Return raw and sanitised migration entries plus warnings."""

    warnings: list[str] = []
    try:
        data = json.loads(matrix_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        warnings.append(f"migration matrix missing at {matrix_path}")
        return [], [], warnings
    except json.JSONDecodeError as exc:
        warnings.append(f"migration matrix at {matrix_path} not valid JSON: {exc}")
        return [], [], warnings

    source_entries = data.get("apsu_migration")
    if not isinstance(source_entries, list):
        warnings.append("component_index.json missing 'apsu_migration' list")
        return [], [], warnings

    tokens = tuple(token.lower() for token in match_tokens)
    raw_entries: list[Mapping[str, Any]] = []
    sanitised: list[dict[str, Any]] = []
    for entry in source_entries:
        if not isinstance(entry, Mapping):
            continue
        neo_module = str(entry.get("neo_module", "")).lower()
        if tokens and not any(token in neo_module for token in tokens):
            continue
        raw_entries.append(entry)
        defects_raw = entry.get("defects")
        if isinstance(defects_raw, Sequence) and not isinstance(
            defects_raw, (str, bytes, bytearray)
        ):
            defects = [str(item) for item in defects_raw]
        elif defects_raw is None:
            defects = []
        else:
            defects = [str(defects_raw)]
        sanitised.append(
            {
                "legacy_entry": entry.get("legacy_entry"),
                "neo_module": entry.get("neo_module"),
                "status": entry.get("status"),
                "defects": defects,
            }
        )

    if not raw_entries:
        warnings.append("no matching migration entries located for Neo-APSU service")

    return raw_entries, sanitised, warnings


def run_contract_suite(module_name: str, **kwargs: Any) -> dict[str, Any]:
    """Invoke ``module_name.run_contract_suite`` with ``kwargs`` if available."""

    module = importlib.import_module(module_name)
    runner = getattr(module, "run_contract_suite", None)
    if not callable(runner):
        return {
            "suite": module_name,
            "status": "unavailable",
            "tests": [],
            "sandbox": bool(getattr(module, "__neoapsu_sandbox__", False)),
            "notes": ["run_contract_suite missing on module"],
        }

    try:
        result = runner(**kwargs)
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("Neo-APSU contract suite '%s' failed", module_name)
        return {
            "suite": module_name,
            "status": "error",
            "tests": [],
            "sandbox": bool(getattr(module, "__neoapsu_sandbox__", False)),
            "notes": [f"contract suite raised {exc.__class__.__name__}: {exc}"],
        }

    if isinstance(result, Mapping):
        return dict(result)
    if isinstance(result, Sequence) and not isinstance(result, (str, bytes, bytearray)):
        return {
            "suite": module_name,
            "status": "ok",
            "tests": list(result),
        }
    return {
        "suite": module_name,
        "status": str(result),
        "tests": [],
        "sandbox": bool(getattr(module, "__neoapsu_sandbox__", False)),
        "notes": ["unexpected contract suite result shape"],
    }


def sanitise_contract_result(
    result: Mapping[str, Any], *, module_name: str
) -> dict[str, Any]:
    """Normalise ``result`` from :func:`run_contract_suite`."""

    suite = str(result.get("suite") or module_name)
    tests_raw = result.get("tests")
    tests: list[dict[str, Any]] = []
    if isinstance(tests_raw, Sequence) and not isinstance(
        tests_raw, (str, bytes, bytearray)
    ):
        for index, item in enumerate(tests_raw, start=1):
            if isinstance(item, Mapping):
                test_id = str(item.get("id") or item.get("name") or index)
                name = str(item.get("name") or item.get("id") or f"test-{index}")
                status = str(item.get("status") or "unknown")
                entry: dict[str, Any] = {
                    "id": test_id,
                    "name": name,
                    "status": status,
                }
                if item.get("reason") is not None:
                    entry["reason"] = _stringify_value(item.get("reason"))
                if item.get("details") is not None:
                    entry["details"] = _stringify_value(item.get("details"))
                tests.append(entry)
            else:
                tests.append(
                    {
                        "id": f"{suite}-{index}",
                        "name": str(item),
                        "status": "unknown",
                    }
                )

    notes_raw = result.get("notes")
    if isinstance(notes_raw, Sequence) and not isinstance(
        notes_raw, (str, bytes, bytearray)
    ):
        notes = [str(note) for note in notes_raw]
    elif notes_raw is None:
        notes = []
    else:
        notes = [str(notes_raw)]

    fixtures_raw = result.get("fixtures")
    fixtures = None
    if isinstance(fixtures_raw, Mapping):
        fixtures = {
            str(key): _stringify_value(val) for key, val in fixtures_raw.items()
        }

    sanitised: dict[str, Any] = {
        "suite": suite,
        "status": str(result.get("status") or "unknown"),
        "tests": tests,
        "notes": notes,
        "sandboxed": bool(
            result.get("sandbox")
            or result.get("sandboxed")
            or result.get("runtime_stubbed")
        ),
    }
    if fixtures is not None:
        sanitised["fixtures"] = fixtures
    return sanitised


def summarise_test_counts(tests: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Return aggregate counts for ``tests``."""

    counts = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
    for test in tests:
        status = str(test.get("status") or "").lower()
        counts["total"] += 1
        if status == "passed":
            counts["passed"] += 1
        elif status in {"failed", "error", "failure"}:
            counts["failed"] += 1
        elif status in {"skipped", "pending", "stubbed"}:
            counts["skipped"] += 1
    return counts


def execute_verification(
    *,
    service: str,
    module_name: str,
    repo_root: Path,
    log_dir: Path,
    run_id: str,
    matrix_path: Path,
    matrix_tokens: Sequence[str],
    overrides: Mapping[str, str],
    sandbox_summary: str,
    contract_kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the Neo-APSU verification workflow and return a summary payload."""

    raw_entries, sanitised_entries, matrix_warnings = load_migration_entries(
        matrix_path, matrix_tokens
    )

    kwargs = dict(contract_kwargs or {})
    kwargs.setdefault("matrix_entries", raw_entries)

    contract_raw = run_contract_suite(module_name, **kwargs)
    contract = sanitise_contract_result(contract_raw, module_name=module_name)
    counts = summarise_test_counts(contract.get("tests", []))
    sandboxed = bool(contract.get("sandboxed")) or module_name in overrides

    warnings = list(matrix_warnings)
    if counts["failed"]:
        warnings.append(f"{counts['failed']} contract test(s) failed")
    if not sanitised_entries:
        warnings.append("no APSU migration entries matched service tokens")
    if sandboxed:
        warnings.append("sandbox stub active for Neo-APSU contracts")

    status = "success"
    if counts["failed"] or not sanitised_entries:
        status = "requires_attention"

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    log_dir.mkdir(parents=True, exist_ok=True)
    service_root = log_dir.parent
    service_root.mkdir(parents=True, exist_ok=True)

    contract_results_path = log_dir / "contract_results.json"
    migration_snapshot_path = log_dir / "migration_snapshot.json"
    run_summary_path = log_dir / "service_summary.json"
    latest_summary_path = service_root / "summary.json"

    _write_json(contract_results_path, contract)
    _write_json(migration_snapshot_path, sanitised_entries)

    summary_contract = {
        "suite": contract.get("suite", module_name),
        "status": contract.get("status", "unknown"),
        "passed": counts["passed"],
        "failed": counts["failed"],
        "skipped": counts["skipped"],
        "total": counts["total"],
        "sandboxed": sandboxed,
        "notes": contract.get("notes", []),
        "tests": contract.get("tests", []),
    }
    if "fixtures" in contract:
        summary_contract["fixtures"] = contract["fixtures"]

    summary = {
        "status": status,
        "service": service,
        "module": module_name,
        "run_id": run_id,
        "generated_at": generated_at,
        "log_dir": str(log_dir),
        "sandbox_summary": sandbox_summary,
        "sandbox_overrides": dict(sorted(overrides.items())),
        "sandboxed": sandboxed,
        "contract_suite": summary_contract,
        "migration_entries": sanitised_entries,
        "warnings": warnings,
    }

    artifacts = {
        "service_summary": str(run_summary_path),
        "latest_summary": str(latest_summary_path),
        "contract_results": str(contract_results_path),
        "migration_snapshot": str(migration_snapshot_path),
    }
    summary["artifacts"] = artifacts

    _write_json(run_summary_path, summary)
    _write_json(latest_summary_path, summary)

    return summary
