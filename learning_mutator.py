from __future__ import annotations

"""Suggest mutations to the intent matrix based on insight metrics."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import emotion_registry

INSIGHT_FILE = Path(__file__).resolve().parent / "insight_matrix.json"
INTENT_FILE = Path(__file__).resolve().parent / "intent_matrix.json"
MUTATION_FILE = Path("data") / "mutations.txt"


def load_insights(path: Path = INSIGHT_FILE) -> Dict[str, Any]:
    """Return insights from ``path`` or an empty mapping."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_intents(path: Path = INTENT_FILE) -> Dict[str, Any]:
    """Return intent matrix data from ``path`` or an empty mapping."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def propose_mutations(insight_matrix: dict) -> List[str]:
    """Return mutation suggestions based on ``insight_matrix``."""
    intents = load_intents()
    rates: Dict[str, tuple[float, int]] = {}
    for pattern, info in insight_matrix.items():
        counts = info.get("counts", {})
        total = counts.get("total", 0)
        success = counts.get("success", 0)
        rate = success / total if total else 0.0
        rates[pattern] = (rate, total)

    high_quality = [p for p, (r, _) in rates.items() if r >= 0.8]
    best = max(high_quality, key=lambda p: rates[p][0]) if high_quality else None

    proposals: List[str] = []
    for pattern, (rate, total) in rates.items():
        if total < 3 or rate >= 0.5:
            continue
        synonyms = intents.get(pattern, {}).get("synonyms", [])
        if synonyms:
            proposals.append(
                f"Replace '{pattern}' with synonym '{synonyms[0]}'"
            )
        elif best and best != pattern:
            proposals.append(
                f"Merge '{pattern}' with high performer '{best}'"
            )

    # Inspect emotional state for potential personality layer changes
    current = emotion_registry.get_current_layer()
    emotion = emotion_registry.get_last_emotion() or "neutral"
    resonance = emotion_registry.get_resonance_level()
    avg_rate = sum(r for r, _ in rates.values()) / len(rates) if rates else 1.0

    if resonance >= 0.8:
        if emotion.lower() in {"anger", "fear", "sadness"}:
            if current != "nigredo_layer":
                proposals.append("Switch to nigredo_layer for shadow work")
        elif emotion.lower() in {"joy", "love"}:
            if current != "rubedo_layer":
                proposals.append("Switch to rubedo_layer for celebratory tone")

    if avg_rate < 0.3 and current:
        proposals.append(f"Fuse {current} with citrinitas_layer for clarity")

    return proposals


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Suggest intent mutations")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Write suggestions to data/mutations.txt",
    )
    parser.add_argument(
        "--activate",
        metavar="LAYER",
        help="Activate personality layer",
    )
    args = parser.parse_args(argv)

    insights = load_insights()
    suggestions = propose_mutations(insights)
    if args.activate:
        emotion_registry.set_current_layer(args.activate)
        print(f"Activated {args.activate}")
        return
    if args.run:
        MUTATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        MUTATION_FILE.write_text("\n".join(suggestions), encoding="utf-8")
        print(f"Wrote {len(suggestions)} suggestions to {MUTATION_FILE}")
    else:
        for s in suggestions:
            print(s)


if __name__ == "__main__":
    main()

__all__ = ["propose_mutations"]
