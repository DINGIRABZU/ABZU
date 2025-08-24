"""Automatically trigger fine-tuning based on feedback metrics.

Monitors evaluation feedback and launches retraining jobs when performance
drops below configured thresholds.
"""

from __future__ import annotations

import argparse
import asyncio
import fnmatch
import json
import logging
import os
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from core import feedback_logging
from core.utils.seed import seed_all
from INANNA_AI.ethical_validator import EthicalValidator
from INANNA_AI.gates import verify_blob
from learning_mutator import propose_mutations

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except ImportError:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]
    vector_memory = _vector_memory
"""Optional vector memory subsystem; ``None`` if unavailable."""

seed_all(int(os.getenv("SEED", "0")))

INSIGHT_FILE = Path("insight_matrix.json")
DATASET_SIGNATURE_FILE = Path("dataset.sig")
PUBLIC_KEY_FILE = Path("dataset.pub")
PERMISSIONS_FILE = Path("permissions.yml")

NOVELTY_THRESHOLD = feedback_logging.NOVELTY_THRESHOLD
COHERENCE_THRESHOLD = feedback_logging.COHERENCE_THRESHOLD
MODEL_REGISTRY_NAME = os.getenv("MODEL_REGISTRY_NAME", "inanna-model")
LOG_FILE = Path("docs/retraining_log.md")


logger = logging.getLogger(__name__)


def pull_latest_data() -> None:
    """Fetch the newest training data using DVC."""
    try:
        subprocess.run(["dvc", "pull"], check=True)
    except Exception:
        logger.exception("failed to pull latest data")


def push_to_registry(model_path: Path) -> str | None:
    """Log and register the trained model artifact via MLflow."""
    try:
        import mlflow
    except Exception:
        logger.error("mlflow is required to push to registry")
        return None
    with mlflow.start_run(run_name="auto_retrain") as run:
        mlflow.log_artifact(str(model_path), artifact_path="model")
        try:
            result = mlflow.register_model(
                f"runs:/{run.info.run_id}/model", MODEL_REGISTRY_NAME
            )
            return getattr(result, "version", run.info.run_id)
        except Exception:
            logger.exception("model registration failed")
            return run.info.run_id


def log_retraining(outcome: str, model_path: Path) -> None:
    """Append retraining outcome and model hash to the log file."""
    try:
        model_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    except Exception:
        model_hash = "unknown"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text(
            "| date | outcome | model_hash |\n| --- | --- | --- |\n",
            encoding="utf-8",
        )
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(
            f"| {datetime.utcnow().isoformat()} | {outcome} | {model_hash} |\n"
        )


def _load_permissions() -> List[Dict[str, List[str]]]:
    try:
        data = yaml.safe_load(PERMISSIONS_FILE.read_text(encoding="utf-8"))
        return data.get("paths", []) if isinstance(data, dict) else []
    except Exception:
        logger.error("permission manifest missing")
        return []


def has_permission(target: Path, operation: str) -> bool:
    try:
        rel = str(target.resolve().relative_to(PERMISSIONS_FILE.parent))
    except ValueError:
        return True
    for entry in _load_permissions():
        pattern = entry.get("path", "")
        ops = entry.get("operations", [])
        if pattern and fnmatch.fnmatch(rel, pattern) and operation in ops:
            return True
    return False


def _load_json(path: Path, default: Any) -> Any:
    if not has_permission(path, "read"):
        logger.error("Permission denied for reading %s", path)
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("failed to load %s", path)
        return default


def compute_metrics(insights: dict, feedback: Iterable[dict]) -> tuple[float, float]:
    """Return novelty and coherence scores from feedback."""
    try:
        entries = list(feedback)
        if not entries:
            return 0.0, 0.0

        known = set(insights)
        intents = [e.get("intent") for e in entries if e.get("intent")]
        new = sum(1 for i in intents if i not in known)
        novelty = new / len(intents) if intents else 0.0

        scores = [e.get("response_quality", 0.0) for e in entries]
        coherence = sum(scores) / len(scores) if scores else 0.0
        return novelty, coherence
    except Exception:
        logger.exception("failed to compute metrics")
        return 0.0, 0.0


def build_dataset(
    feedback: Iterable[dict], validator: EthicalValidator | None = None
) -> list[dict]:
    """Return a fine-tuning dataset from successful feedback entries."""
    validator = validator or EthicalValidator()
    try:
        dataset = []
        for entry in feedback:
            intent = entry.get("intent")
            action = entry.get("action")
            if entry.get("success") and intent and action:
                if validator.validate_text(intent) and validator.validate_text(action):
                    dataset.append({"prompt": intent, "completion": action})
        try:
            for proposal in propose_mutations(_load_json(INSIGHT_FILE, {})):
                if validator.validate_text(proposal):
                    dataset.append({"prompt": "PATCH", "completion": proposal})
        except Exception:
            logger.exception("failed to add mutation proposals")
        return dataset
    except Exception:
        logger.exception("failed to build dataset")
        return []


def _load_vector_logs() -> List[Dict[str, Any]]:
    if vector_memory is None:
        return []
    if not has_permission(vector_memory.LOG_FILE, "read"):
        logger.error("Permission denied for reading %s", vector_memory.LOG_FILE)
        return []
    if not vector_memory.LOG_FILE.exists():
        return []
    entries = []
    with vector_memory.LOG_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                entries.append(json.loads(line))
            except Exception:
                logger.error("invalid json line in %s", vector_memory.LOG_FILE)
    return entries


def system_idle() -> bool:
    """Return ``True`` if no training lock file exists."""
    lock = Path("training.lock")
    if not has_permission(lock, "read"):
        logger.error("Permission denied for reading %s", lock)
        return False
    return not lock.exists()


def verify_signature(dataset: list[dict]) -> bool:
    """Return ``True`` if ``dataset`` matches ``DATASET_SIGNATURE_FILE``."""
    try:
        if not (
            has_permission(DATASET_SIGNATURE_FILE, "read")
            and has_permission(PUBLIC_KEY_FILE, "read")
        ):
            logger.error("Permission denied for signature files")
            return False
        sig = DATASET_SIGNATURE_FILE.read_bytes()
        pub = PUBLIC_KEY_FILE.read_bytes()
        payload = json.dumps(dataset, sort_keys=True).encode("utf-8")
        return verify_blob(payload, sig, pub)
    except Exception:
        logger.exception("signature verification failed")
        return False


def trigger_finetune(
    dataset: list[dict], validator: EthicalValidator | None = None
) -> Path | None:
    """Invoke the LLM fine-tuning API with ``dataset``."""
    validator = validator or EthicalValidator()
    try:
        for item in dataset:
            if not (
                validator.validate_text(item.get("prompt", ""))
                and validator.validate_text(item.get("completion", ""))
            ):
                logger.error("Dataset contains disallowed content")
                return None
        if not verify_signature(dataset):
            logger.error("dataset signature invalid")
            return None
        import llm_api

        try:
            artifact = llm_api.fine_tune(dataset)
            return Path(artifact) if artifact else None
        except Exception:
            rollback = getattr(llm_api, "rollback", None)
            if callable(rollback):
                try:
                    rollback()
                except Exception:
                    logger.exception("rollback failed")
            raise
    except Exception:
        logger.exception("failed to trigger fine-tune")
        return None


async def retrain_model(dataset: list[dict], *, run_name: str | None = None) -> None:
    """Fine-tune the model on ``dataset`` while logging an MLflow run.

    This asynchronous routine logs the run via MLflow and reloads updated
    embeddings in the vector memory subsystem once training completes.

    Parameters
    ----------
    dataset:
        Training examples used for supervised self-improvement.
    run_name:
        Optional MLflow run name. Defaults to ``"auto_retrain"``.
    """
    try:
        import mlflow
    except Exception:  # pragma: no cover - optional dependency
        logger.error("mlflow is required for retrain_model")
        return

    name = run_name or "auto_retrain"
    with mlflow.start_run(run_name=name):
        mlflow.log_param("examples", len(dataset))
        await asyncio.to_thread(trigger_finetune, dataset)
        if _vector_memory is not None:
            await asyncio.to_thread(
                _vector_memory.configure, embedder=_vector_memory._EMBED
            )


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI entry
    parser = argparse.ArgumentParser(description="Automatically retrain model")
    parser.add_argument("--run", action="store_true", help="Execute fine-tuning")
    parser.add_argument("--dry-run", action="store_true", help="Show dataset only")
    args = parser.parse_args(argv)

    pull_latest_data()

    insights = _load_json(INSIGHT_FILE, {})
    feedback = feedback_logging.load_feedback()
    vector_entries = _load_vector_logs()

    novelty, coherence = compute_metrics(insights, feedback)
    logger.info("Novelty: %.2f Coherence: %.2f", novelty, coherence)

    if (
        novelty >= NOVELTY_THRESHOLD
        and coherence >= COHERENCE_THRESHOLD
        and vector_entries
        and system_idle()
    ):
        validator = EthicalValidator()
        dataset = build_dataset(feedback, validator)
        if args.run:
            model_path = trigger_finetune(dataset, validator)
            if model_path:
                registry_id = push_to_registry(model_path)
                outcome = f"registered {registry_id}" if registry_id else "trained"
                log_retraining(outcome, model_path)
                logger.info("Fine-tuning triggered")
            else:
                logger.error("Fine-tuning failed")
        else:
            logger.info(json.dumps(dataset, indent=2))
    else:
        logger.info("Conditions not met")


if __name__ == "__main__":  # pragma: no cover - manual run
    main()
