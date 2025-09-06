"""Service manifest loader for per-world settings."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class ServiceManifest:
    """Configuration for services bound to a world."""

    model: str | None = None
    tokenizer: str | None = None
    vector_db: Dict[str, Any] | None = None
    event_bus: Dict[str, Any] | None = None


def load_manifest(path: Path) -> Dict[str, ServiceManifest]:
    """Load service manifest mapping worlds to configurations."""

    if not path.exists():
        logging.debug("services manifest %s missing", path)
        return {}
    data = yaml.safe_load(path.read_text("utf-8")) or {}
    manifest: Dict[str, ServiceManifest] = {}
    for world, cfg in data.items():
        manifest[world] = ServiceManifest(
            model=cfg.get("model"),
            tokenizer=cfg.get("tokenizer"),
            vector_db=cfg.get("vector_db"),
            event_bus=cfg.get("event_bus"),
        )
    return manifest


def warn_missing_services(manifest: Dict[str, ServiceManifest], world: str) -> None:
    """Emit warnings for undefined services for ``world``."""

    services = manifest.get(world)
    if services is None:
        logging.warning("world %s has no service manifest", world)
        return
    required = ("model", "tokenizer", "vector_db", "event_bus")
    for name in required:
        if getattr(services, name) is None:
            logging.warning("world %s missing %s configuration", world, name)


__all__ = ["load_manifest", "warn_missing_services", "ServiceManifest"]
