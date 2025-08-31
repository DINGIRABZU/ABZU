from __future__ import annotations

__version__ = "0.2.2"

"""Planner that consolidates blueprints, failures, and Crown suggestions.

The planner reads component priorities from ``docs/component_priorities.yaml``,
recent failure counts from ``logs/razar_boot_history.json`` and advisory notes
from ``logs/razar_crown_dialogues.json``. It produces a dependency ordered build
plan and appends it to ``logs/razar_cocreation_plans.json``.

This module is intentionally lightweight and acts as a scaffold for future
integration with the RAZAR runtime manager.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

LOGGER = logging.getLogger("razar.cocreation_planner")

ROOT = Path(__file__).resolve().parents[1]
PRIORITY_PATH = ROOT / "docs" / "component_priorities.yaml"
FAILURE_PATH = ROOT / "logs" / "razar_boot_history.json"
CROWN_PATH = ROOT / "logs" / "razar_crown_dialogues.json"
PLAN_PATH = ROOT / "logs" / "razar_cocreation_plans.json"


def _parse_priority(value: str) -> int:
    """Return numeric value from priority label like ``P1``."""

    try:
        return int(value.lstrip("P"))
    except Exception:  # pragma: no cover - defensive
        return 999


def load_components(path: Path = PRIORITY_PATH) -> Dict[str, int]:
    """Load component priorities from ``path``."""

    data: Dict[str, Dict[str, Any]] = yaml.safe_load(path.read_text())
    return {
        name: _parse_priority(info.get("priority", "P999"))
        for name, info in data.items()
    }


def load_failures(path: Path = FAILURE_PATH) -> Dict[str, Any]:
    """Return failure metadata keyed by component name."""

    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("component_failures", {})


def load_crown_suggestions(path: Path = CROWN_PATH) -> Dict[str, List[str]]:
    """Return Crown LLM suggestions grouped by component."""

    if not path.exists():
        return {}
    try:
        entries: List[Dict[str, Any]] = json.loads(path.read_text())
    except json.JSONDecodeError:  # pragma: no cover - defensive
        return {}
    suggestions: Dict[str, List[str]] = {}
    for entry in entries:
        module = entry.get("module")
        text = entry.get("suggestion")
        if not module or not text:
            continue
        suggestions.setdefault(module, []).append(text)
    return suggestions


def build_plan() -> List[Dict[str, Any]]:
    """Construct a dependency ordered plan from available records."""

    components = load_components()
    failures = load_failures()
    suggestions = load_crown_suggestions()

    ordered = sorted(components.items(), key=lambda item: item[1])
    plan: List[Dict[str, Any]] = []
    for comp, priority in ordered:
        deps = [name for name, pr in components.items() if pr < priority]
        step: Dict[str, Any] = {
            "component": comp,
            "priority": f"P{priority}",
            "depends_on": deps,
        }
        if comp in failures:
            step["failures"] = failures[comp]
        if comp in suggestions:
            step["crown_suggestions"] = suggestions[comp]
        plan.append(step)
    return plan


def save_plan(plan: List[Dict[str, Any]], path: Path = PLAN_PATH) -> None:
    """Append ``plan`` to the history at ``path``."""

    history = {"plans": []}
    if path.exists():
        try:
            history = json.loads(path.read_text())
        except json.JSONDecodeError:  # pragma: no cover - defensive
            LOGGER.warning("Invalid JSON in %%s; overwriting", path)
    history.setdefault("plans", []).append(
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "steps": plan,
        }
    )
    path.write_text(json.dumps(history, indent=2))


def run() -> List[Dict[str, Any]]:
    """Generate and persist a co-creation plan."""

    plan = build_plan()
    save_plan(plan)
    LOGGER.info("Wrote plan with %d steps to %s", len(plan), PLAN_PATH)
    return plan


if __name__ == "__main__":  # pragma: no cover - module CLI
    run()
