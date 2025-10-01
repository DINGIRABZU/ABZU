"""Stage D sandbox verification for the Neo-APSU identity bridge."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts import _stage_runtime as stage_runtime  # noqa: E402 (bootstrap first)
from scripts._neoapsu_verifier import execute_verification

LOGGER = logging.getLogger("neoapsu.verify.identity")
SERVICE = "neoapsu_identity"
MODULE = "neoapsu_identity"
MATRIX_TOKENS = (
    "neoapsu_identity",
    "neoabzu_identity",
    "neoabzu_crown::load_identity",
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        type=Path,
        help="Path to component_index.json (defaults to <repo>/component_index.json)",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Optional identity fixture forwarded to the contract suite",
    )
    parser.add_argument(
        "--run-id",
        help="Explicit run identifier. Defaults to <timestamp>-neoapsu_identity.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        help=(
            "Directory for run artifacts. Defaults to "
            "logs/stage_d/neoapsu_identity/<run_id>"
        ),
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Force sandbox overrides and emit a summary of active stubs.",
    )
    return parser.parse_args(argv)


def _resolve_run_context(
    repo_root: Path, run_id_arg: str | None, log_dir_arg: Path | None
) -> tuple[str, Path]:
    if log_dir_arg is not None:
        log_dir = Path(log_dir_arg)
        run_id = run_id_arg or log_dir.name
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = run_id_arg or f"{timestamp}-{SERVICE}"
        log_dir = repo_root / "logs" / "stage_d" / SERVICE / run_id
    return run_id, log_dir


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

    sandbox_logger = logging.getLogger("neoapsu.verify.identity.sandbox")
    repo_root = stage_runtime.bootstrap(
        optional_modules=[MODULE],
        sandbox=True if args.sandbox else None,
        log_summary=bool(args.sandbox),
        summary_logger=sandbox_logger,
    )

    matrix_path = (
        Path(args.matrix) if args.matrix else repo_root / "component_index.json"
    )
    run_id, log_dir = _resolve_run_context(repo_root, args.run_id, args.log_dir)

    contract_kwargs: dict[str, Any] = {}
    if args.fixture is not None:
        fixture_path = Path(args.fixture)
        if fixture_path.exists():
            contract_kwargs["fixture_path"] = str(fixture_path)
        else:
            LOGGER.warning(
                "fixture path %s not found; continuing without fixture", fixture_path
            )

    overrides = stage_runtime.get_sandbox_overrides()
    sandbox_summary = stage_runtime.format_sandbox_summary("Neo-APSU sandbox")

    summary = execute_verification(
        service=SERVICE,
        module_name=MODULE,
        repo_root=repo_root,
        log_dir=log_dir,
        run_id=run_id,
        matrix_path=matrix_path,
        matrix_tokens=MATRIX_TOKENS,
        overrides=overrides,
        sandbox_summary=sandbox_summary,
        contract_kwargs=contract_kwargs,
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary.get("status") == "success" else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
