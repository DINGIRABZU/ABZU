"""Benchmark a minimal training and inference step."""

from __future__ import annotations

import json
from pathlib import Path

import torch


def train_step(device: str) -> None:
    model = torch.nn.Linear(10, 1).to(device)
    opt = torch.optim.SGD(model.parameters(), lr=0.01)
    data = torch.randn(16, 10, device=device)
    target = torch.randn(16, 1, device=device)

    opt.zero_grad()
    out = model(data)
    loss = torch.nn.functional.mse_loss(out, target)
    loss.backward()
    opt.step()


def test_train_infer(benchmark) -> None:
    """Benchmark a single training step and log the result."""
    device = (
        "cuda"
        if torch.cuda.is_available()
        else ("xpu" if hasattr(torch, "xpu") and torch.xpu.is_available() else "cpu")
    )
    benchmark(lambda: train_step(device))
    stats = benchmark.stats.stats

    out_dir = Path("data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "train_infer.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump({"mean": stats.mean, "stddev": stats.stddev}, f)
