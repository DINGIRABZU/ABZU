from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

__version__ = "0.1.0"

REQUIRED_PANEL_KEYS = {"type", "title", "targets"}
REQUIRED_TARGET_KEYS = {"expr"}


def _load_dashboard(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: dashboard root must be a JSON object")
    return data


def _validate_dashboard(path: Path, data: dict[str, object]) -> list[str]:
    errors: list[str] = []

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("missing or empty title")

    panels = data.get("panels")
    if not isinstance(panels, list) or not panels:
        errors.append("panels must be a non-empty list")
    else:
        for idx, panel in enumerate(panels):
            if not isinstance(panel, dict):
                errors.append(f"panel[{idx}] must be a JSON object")
                continue
            missing_panel_keys = sorted(REQUIRED_PANEL_KEYS - panel.keys())
            if missing_panel_keys:
                errors.append(
                    f"panel[{idx}] missing keys: {', '.join(missing_panel_keys)}"
                )
            targets = panel.get("targets")
            if not isinstance(targets, list) or not targets:
                errors.append(f"panel[{idx}].targets must be a non-empty list")
                continue
            for target_idx, target in enumerate(targets):
                if not isinstance(target, dict):
                    errors.append(
                        f"panel[{idx}].targets[{target_idx}] must be a JSON object"
                    )
                    continue
                missing_target_keys = sorted(REQUIRED_TARGET_KEYS - target.keys())
                if missing_target_keys:
                    errors.append(
                        f"panel[{idx}].targets[{target_idx}] missing keys: {', '.join(missing_target_keys)}"
                    )
                expr = target.get("expr")
                if not isinstance(expr, str) or not expr.strip():
                    errors.append(
                        f"panel[{idx}].targets[{target_idx}].expr must be a non-empty string"
                    )

    templating = data.get("templating")
    if not isinstance(templating, dict):
        errors.append("templating must be a JSON object containing dashboard variables")
    else:
        variables = templating.get("list")
        if not isinstance(variables, list) or not variables:
            errors.append("templating.list must be a non-empty list")
        else:
            names = {
                item.get("name")
                for item in variables
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            }
            if "component" not in names:
                errors.append("templating.list must define a 'component' variable")

    return errors


def _iter_dashboards(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.json") if p.is_file())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Grafana dashboard JSON files so CI can catch schema regressions"
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "monitoring" / "grafana",
        help="Directory containing dashboard JSON files",
    )
    args = parser.parse_args(argv)

    dashboards = _iter_dashboards(args.root)
    if not dashboards:
        parser.error(f"no dashboards found under {args.root}")

    total_errors = 0
    for dashboard_path in dashboards:
        try:
            data = _load_dashboard(dashboard_path)
        except ValueError as exc:
            print(exc)
            total_errors += 1
            continue
        errors = _validate_dashboard(dashboard_path, data)
        for message in errors:
            print(f"{dashboard_path}: {message}")
        total_errors += len(errors)

    if total_errors:
        print(f"Validation failed with {total_errors} issue(s).")
        return 1

    print(f"Validated {len(dashboards)} dashboard(s) under {args.root}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
