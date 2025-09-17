#!/usr/bin/env python3
"""Refresh the Crown identity summary and fingerprint."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import init_crown_agent as crown_init
from INANNA_AI.glm_integration import GLMIntegration
from identity_loader import (
    DOCTRINE_DOCS,
    HANDSHAKE_PROMPT,
    HANDSHAKE_TOKEN,
    IDENTITY_FILE,
)
from neoabzu_crown import load_identity

LOG_DIR = Path("logs/identity_refresh")
DEFAULT_LOG_LEVEL = "INFO"


class _DigestingStub:
    """Deterministic GLM stub that encodes the prompt hash."""

    endpoint = "stub://glm"

    def complete(
        self, prompt: str, *, quantum_context: str | None = None
    ) -> str:  # noqa: D401
        """Return a deterministic response derived from ``prompt``."""

        if prompt.strip() == HANDSHAKE_PROMPT.strip():
            return HANDSHAKE_TOKEN
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return f"[crown-identity-stub {digest}]"


def _configure_logging(level: str, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(formatter)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers = [handler, console]


def _load_configuration(
    overrides: argparse.Namespace,
) -> tuple[dict, GLMIntegration | _DigestingStub]:
    if overrides.use_stub:
        logging.info("Using deterministic GLM stub integration")
        return {}, _DigestingStub()

    cfg = crown_init._load_config()  # type: ignore[attr-defined]
    endpoint = overrides.glm_endpoint or cfg.get("glm_api_url")
    api_key = overrides.glm_api_key or cfg.get("glm_api_key")

    if cfg.get("model_path"):
        os.environ.setdefault("MODEL_PATH", str(cfg["model_path"]))

    crown_init._init_memory(cfg)  # type: ignore[attr-defined]

    logging.info(
        "Initializing GLM integration targeting %s",
        endpoint or GLMIntegration.DEFAULT_ENDPOINT,
    )
    glm = GLMIntegration(endpoint=endpoint, api_key=api_key)
    return cfg, glm


def _remove_cached_identity(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.exists():
            logging.info("Removing cached artifact at %s", path)
            path.unlink()


def _refresh_identity(glm: GLMIntegration | _DigestingStub) -> dict[str, str]:
    crown_init._update_identity_ready_metric(None, None)  # type: ignore[attr-defined]
    summary = load_identity(glm)
    crown_init._store_identity_summary(summary)  # type: ignore[attr-defined]
    fingerprint = crown_init._compute_identity_fingerprint()  # type: ignore[attr-defined]
    if not fingerprint:
        raise RuntimeError("Failed to compute identity fingerprint")
    crown_init._publish_identity_fingerprint(fingerprint)  # type: ignore[attr-defined]
    crown_init._update_identity_ready_metric(summary, fingerprint)  # type: ignore[attr-defined]
    return fingerprint


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Skip clearing cached identity artifacts before regeneration.",
    )
    parser.add_argument(
        "--glm-endpoint",
        help="Override the GLM endpoint discovered from configuration.",
    )
    parser.add_argument(
        "--glm-api-key",
        help="Explicit GLM API key to use for the refresh.",
    )
    parser.add_argument(
        "--use-stub",
        action="store_true",
        help="Use the deterministic GLM stub instead of reaching a live endpoint.",
    )
    parser.add_argument(
        "--log-level",
        default=DEFAULT_LOG_LEVEL,
        help="Logging verbosity (default: %(default)s).",
    )
    parser.add_argument(
        "--log-dir",
        default=str(LOG_DIR),
        help="Directory where refresh logs are written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = Path(args.log_dir) / f"refresh_{timestamp}.log"
    _configure_logging(args.log_level, log_path)

    logging.info("Starting Crown identity refresh")
    logging.info("Log file: %s", log_path)

    if not args.keep_existing:
        _remove_cached_identity(
            [
                IDENTITY_FILE,
                crown_init.FINGERPRINT_STATE_PATH,  # type: ignore[attr-defined]
            ]
        )

    try:
        _cfg, glm = _load_configuration(args)
        logging.debug(
            "Doctrine corpus monitored for refresh: %s",
            ", ".join(str(path) for path in DOCTRINE_DOCS),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logging.exception("Failed to prepare GLM integration: %s", exc)
        return 2

    try:
        fingerprint = _refresh_identity(glm)
    except Exception as exc:  # pragma: no cover - defensive
        logging.exception("Identity refresh failed: %s", exc)
        return 3

    payload_data = {"fingerprint": fingerprint, "log_path": str(log_path)}
    payload = json.dumps(payload_data, indent=2)
    logging.info("Identity fingerprint: %s", json.dumps(fingerprint, sort_keys=True))
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
