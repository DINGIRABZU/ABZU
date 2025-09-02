"""Evaluate pretrained emotion models on a labelled dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from INANNA_AI.emotion_analysis import predict_emotion_ml


def _iter_dataset(root: Path) -> Iterable[Tuple[str, str]]:
    """Yield ``(path, label)`` pairs from ``root``.

    The directory must contain subdirectories named after emotion labels. Each
    subdirectory is searched for ``.wav`` files which are associated with the
    label given by the directory name.
    """

    for label_dir in root.iterdir():
        if not label_dir.is_dir():
            continue
        label = label_dir.name
        for wav in label_dir.glob("*.wav"):
            yield str(wav), label


def evaluate_model(model_name: str, data: Iterable[Tuple[str, str]]) -> float:
    """Return the accuracy for ``model_name`` on ``data``."""

    total = 0
    correct = 0
    for path, label in data:
        total += 1
        try:
            probs = predict_emotion_ml(path, model_name)
            pred = max(probs, key=probs.get)
        except Exception:
            pred = None
        if pred == label:
            correct += 1
    return correct / total if total else 0.0


def main() -> None:  # pragma: no cover - CLI utility
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate emotion models")
    parser.add_argument("dataset", type=Path, help="Path to labelled dataset")
    parser.add_argument(
        "--model",
        dest="models",
        action="append",
        default=["m-a-p/MERT-v1-330M-CLAP", "laion/clap-htsat-unfused"],
        help="Hugging Face model identifiers",
    )
    args = parser.parse_args()

    dataset = list(_iter_dataset(args.dataset))
    for m in args.models:
        acc = evaluate_model(m, dataset)
        print(f"{m}: accuracy={acc:.3f}")


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
