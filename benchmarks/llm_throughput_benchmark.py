from __future__ import annotations

"""Benchmark transformer throughput in tokens per second."""

import json
import sys
import time
from pathlib import Path

import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))


def benchmark_llm(
    seq_len: int = 128, batch_size: int = 1, d_model: int = 64
) -> dict[str, float]:
    """Run a tiny transformer encoder once and measure tokens per second."""
    layer = torch.nn.TransformerEncoderLayer(d_model=d_model, nhead=4)
    model = torch.nn.TransformerEncoder(layer, num_layers=2)
    tokens = torch.randn(seq_len, batch_size, d_model)

    start = time.perf_counter()
    with torch.no_grad():
        model(tokens)
    duration = time.perf_counter() - start

    tokens_processed = seq_len * batch_size
    metrics = {
        "tokens_per_sec": round(tokens_processed / duration if duration else 0.0, 2)
    }
    out_dir = Path("data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "llm_throughput.json"
    out_file.write_text(json.dumps(metrics))
    return metrics


def main() -> None:
    metrics = benchmark_llm()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
