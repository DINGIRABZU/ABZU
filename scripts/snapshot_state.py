from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

__all__ = ["create_snapshot", "restore_snapshot"]


def _load_agent_registry(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _load_doctrine_versions(path: Path) -> Dict[str, str]:
    versions: Dict[str, str] = {}
    if not path.exists():
        return versions
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2:
            file_name, version = parts[0], parts[1]
            versions[file_name] = version
    return versions


def _load_vector_snapshot() -> Dict[str, Any]:
    try:
        from vector_memory import persist_snapshot  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return {}
    try:
        path = persist_snapshot()
    except Exception:  # pragma: no cover - snapshot best effort
        return {}
    return {"snapshot": str(path)}


def create_snapshot(
    out_dir: str | Path = "storage/snapshots",
    *,
    registry_file: str | Path = "agents/nazarick/agent_registry.json",
    doctrine_index: str | Path = "docs/doctrine_index.md",
) -> Path:
    """Serialize key state into ``out_dir`` and return the snapshot path."""

    data = {
        "agent_registry": _load_agent_registry(Path(registry_file)),
        "doctrine_versions": _load_doctrine_versions(Path(doctrine_index)),
        "vector_embeddings": _load_vector_snapshot(),
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    snap_path = out / f"snapshot_{int(time.time())}.json"
    snap_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return snap_path


def restore_snapshot(
    snapshot_file: str | Path,
    *,
    registry_file: str | Path = "agents/nazarick/agent_registry.json",
    doctrine_versions_file: str | Path | None = None,
    vector_embeddings_file: str | Path | None = None,
) -> Dict[str, Any]:
    """Restore state from ``snapshot_file`` and return the data."""

    data: Dict[str, Any] = json.loads(Path(snapshot_file).read_text(encoding="utf-8"))
    Path(registry_file).parent.mkdir(parents=True, exist_ok=True)
    Path(registry_file).write_text(
        json.dumps(data.get("agent_registry", {}), ensure_ascii=False),
        encoding="utf-8",
    )
    if doctrine_versions_file is not None:
        Path(doctrine_versions_file).parent.mkdir(parents=True, exist_ok=True)
        Path(doctrine_versions_file).write_text(
            json.dumps(data.get("doctrine_versions", {}), ensure_ascii=False),
            encoding="utf-8",
        )
    if vector_embeddings_file is not None:
        Path(vector_embeddings_file).parent.mkdir(parents=True, exist_ok=True)
        Path(vector_embeddings_file).write_text(
            json.dumps(data.get("vector_embeddings", {}), ensure_ascii=False),
            encoding="utf-8",
        )
    return data


if __name__ == "__main__":  # pragma: no cover - manual usage
    path = create_snapshot()
    print(f"snapshot written to {path}")
