"""Distributed training example using PyTorch FSDP.

This script demonstrates how to configure a distributed training
run through OmegaConf, perform hyperparameter optimisation with
Optuna, and log metrics to MLflow.

Example
-------
Run single training job on two GPUs::

    torchrun --nproc_per_node 2 scripts/train_distributed.py --config config/train.yaml

Run hyperparameter sweep::

    python scripts/train_distributed.py --config config/train.yaml --sweep
"""

from __future__ import annotations

import argparse
from pathlib import Path

import mlflow
import optuna
import torch
import torch.distributed as dist
from omegaconf import OmegaConf
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.utils.data import DataLoader, DistributedSampler, TensorDataset


def setup_distributed() -> None:
    """Initialise the distributed process group if needed."""
    if dist.is_available() and not dist.is_initialized():
        backend = "nccl" if torch.cuda.is_available() else "gloo"
        dist.init_process_group(backend=backend)


def cleanup_distributed() -> None:
    """Clean up the distributed process group."""
    if dist.is_initialized():
        dist.destroy_process_group()


def build_dataloader(cfg: OmegaConf) -> DataLoader:
    """Create a simple random data loader for demonstration."""
    samples = cfg.get("samples", 64)
    x = torch.randn(samples, cfg.input_dim)
    y = torch.randn(samples, cfg.output_dim)
    dataset = TensorDataset(x, y)
    if dist.is_initialized():
        sampler = DistributedSampler(dataset)
    else:
        sampler = None
    return DataLoader(dataset, batch_size=cfg.batch_size, sampler=sampler, shuffle=sampler is None)


def train_once(cfg: OmegaConf) -> float:
    """Run a single training loop and return the final loss."""
    setup_distributed()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rank = dist.get_rank() if dist.is_initialized() else 0

    model = torch.nn.Linear(cfg.input_dim, cfg.output_dim).to(device)
    model = FSDP(model)
    dataloader = build_dataloader(cfg)

    optimiser = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    loss_fn = torch.nn.MSELoss()

    final_loss = 0.0
    for epoch in range(cfg.epochs):
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            optimiser.zero_grad()
            output = model(x)
            loss = loss_fn(output, y)
            loss.backward()
            optimiser.step()
            final_loss = loss.item()
        if rank == 0:
            mlflow.log_metric("loss", final_loss, step=epoch)

    cleanup_distributed()
    return final_loss


def run_sweep(cfg: OmegaConf) -> None:
    """Execute an Optuna hyperparameter sweep."""
    sweep_cfg = cfg.sweep

    def objective(trial: optuna.Trial) -> float:
        cfg.lr = trial.suggest_float("lr", sweep_cfg.lr_min, sweep_cfg.lr_max, log=True)
        with mlflow.start_run(nested=True):
            mlflow.log_params({"lr": cfg.lr, "batch_size": cfg.batch_size})
            return train_once(cfg)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=sweep_cfg.trials)
    if dist.get_rank() if dist.is_initialized() else 0 == 0:
        print("Best parameters:", study.best_params)


def main() -> None:
    parser = argparse.ArgumentParser(description="Distributed trainer")
    parser.add_argument("--config", type=Path, required=True, help="Path to config file")
    parser.add_argument("--sweep", action="store_true", help="Run Optuna sweep")
    args = parser.parse_args()

    cfg = OmegaConf.load(args.config)
    mlflow.set_experiment(cfg.get("experiment", "distributed-training"))

    if args.sweep:
        run_sweep(cfg)
    else:
        with mlflow.start_run():
            mlflow.log_params({"lr": cfg.lr, "batch_size": cfg.batch_size})
            final_loss = train_once(cfg)
            mlflow.log_metric("final_loss", final_loss)


if __name__ == "__main__":
    main()
