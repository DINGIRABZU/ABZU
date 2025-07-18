from __future__ import annotations

"""Automate fine-tuning and deployment of INANNA models."""

from datetime import datetime
from pathlib import Path
import os
import shutil
import argparse

from . import train_soul
from .corpus_memory import CHROMA_DIR
from . import config

import mlflow

# Location of versioned soul artifacts and metadata
SOUL_DIR = config.MODELS_DIR / "soul"
SOUL_DIR.mkdir(parents=True, exist_ok=True)
LAST_TRAIN_FILE = SOUL_DIR / "last_trained.txt"
SOUL_FILE = Path(__file__).resolve().parents[1] / "INANNA_AI" / "soul.dna"


def _latest_mod_time(path: Path) -> float:
    latest = 0.0
    if path.exists():
        for root, _dirs, files in os.walk(path):
            for name in files:
                t = (Path(root) / name).stat().st_mtime
                if t > latest:
                    latest = t
    return latest


def has_new_embeddings() -> bool:
    """Return ``True`` if ``CHROMA_DIR`` contains files newer than last run."""
    if not LAST_TRAIN_FILE.exists():
        return True
    last = datetime.fromisoformat(LAST_TRAIN_FILE.read_text().strip())
    return _latest_mod_time(CHROMA_DIR) > last.timestamp()


def _record_timestamp() -> None:
    LAST_TRAIN_FILE.write_text(datetime.utcnow().isoformat())


def retrain_and_deploy(iterations: int = 3) -> None:
    """Fine-tune the soul grid if new embeddings exist and log with MLflow."""
    if not has_new_embeddings():
        print("No new embeddings detected")
        return

    mlflow.start_run()
    mlflow.log_param("iterations", iterations)
    train_soul.train_soul(Path("QNL_LANGUAGE/interactions/log.txt"), iterations)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = SOUL_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / "soul.dna"
    shutil.copy(SOUL_FILE, artifact)
    mlflow.log_artifact(str(artifact))
    mlflow.end_run()

    _record_timestamp()


def rollback(version: str) -> None:
    """Restore ``soul.dna`` from ``version`` under ``SOUL_DIR``."""
    src = SOUL_DIR / version / "soul.dna"
    if not src.exists():
        raise FileNotFoundError(f"version {version} not found")
    shutil.copy(src, SOUL_FILE)
    _record_timestamp()


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI
    parser = argparse.ArgumentParser(description="Retrain INANNA models")
    parser.add_argument("--iterations", type=int, default=3, help="Training steps")
    parser.add_argument("--rollback", help="Rollback to previous version")
    args = parser.parse_args(argv)

    if args.rollback:
        rollback(args.rollback)
    else:
        retrain_and_deploy(args.iterations)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
