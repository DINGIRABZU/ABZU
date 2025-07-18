from __future__ import annotations

"""Cluster spiral memory vectors into archetypal groups."""

from collections import Counter
from pathlib import Path
import argparse
import json
import re
from typing import Any, Iterable

import numpy as np
from sklearn.cluster import KMeans

from MUSIC_FOUNDATION import qnl_utils
import vector_memory

_OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "archetype_clusters.json"


def _tokenize(text: str) -> Iterable[str]:
    return re.findall(r"\b\w+\b", text.lower())


def cluster_vectors(k: int = 5, limit: int = 100) -> list[dict[str, Any]]:
    """Cluster recent vectors and return summary data."""
    records = vector_memory.query_vectors(limit=limit)
    if not records:
        return []

    texts = [str(r.get("text", "")) for r in records]
    emotions = [str(r.get("emotion", "")) for r in records]
    embeddings = np.vstack([qnl_utils.quantum_embed(t) for t in texts])

    km = KMeans(n_clusters=k, n_init="auto", random_state=0)
    labels = km.fit_predict(embeddings)

    summaries: list[dict[str, Any]] = []
    for idx in range(k):
        inds = np.where(labels == idx)[0]
        if inds.size == 0:
            continue
        words: list[str] = []
        cluster_emotions: list[str] = []
        for i in inds:
            words.extend(_tokenize(texts[i]))
            if emotions[i]:
                cluster_emotions.append(emotions[i])
        common_words = [w for w, _ in Counter(words).most_common(5)]
        common_emotions = [e for e, _ in Counter(cluster_emotions).most_common(3)]
        summaries.append(
            {
                "cluster": int(idx),
                "count": int(inds.size),
                "top_terms": common_words,
                "emotions": common_emotions,
            }
        )
    return summaries


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Cluster vector memory entries")
    parser.add_argument("--k", type=int, default=5, help="Number of clusters")
    parser.add_argument(
        "--limit", type=int, default=100, help="Number of recent vectors to process"
    )
    args = parser.parse_args(argv)
    result = cluster_vectors(k=args.k, limit=args.limit)
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {len(result)} clusters to {_OUTPUT_PATH}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
