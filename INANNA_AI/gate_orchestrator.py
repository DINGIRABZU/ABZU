"""Simple gate orchestrator translating text to/from complex vectors."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from time import perf_counter
from typing import Deque, List, Sequence

import numpy as np

from core.utils.optional_deps import lazy_import

torch = lazy_import("torch")
if getattr(torch, "__stub__", False):  # pragma: no cover - optional dependency
    nn = None  # type: ignore[assignment]
else:  # pragma: no cover - optional dependency
    from torch import nn

from . import db_storage

if nn is not None:

    class _ModelPredictor(nn.Module):
        """Tiny LSTM model predicting the best LLM."""

        def __init__(
            self, num_features: int = 4, hidden_size: int = 16, num_models: int = 3
        ) -> None:
            super().__init__()
            self.lstm = nn.LSTM(num_features, hidden_size, batch_first=True)
            self.fc = nn.Linear(hidden_size, num_models)

        def forward(
            self, x: torch.Tensor
        ) -> torch.Tensor:  # pragma: no cover - depends on torch
            out, _ = self.lstm(x)
            return self.fc(out[:, -1])

else:  # pragma: no cover - torch missing

    class _ModelPredictor:  # type: ignore[no-redef]
        def __init__(self, *_, **__):
            raise RuntimeError("torch library is required for GateOrchestrator")


class GateOrchestrator:
    """Map between text and complex vectors for the RFA7D core."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        self._db_path = db_path or db_storage.DB_PATH
        self._context: Deque[List[float]] = deque(maxlen=5)
        self._predictor = None if nn is None else _ModelPredictor()
        self._selection_weights = np.ones(3, dtype=float)
        self._seq_len = 3
        if self._predictor is not None:
            self._train_predictor()
            self._optimize_parameters()

    def process_inward(self, text: str) -> Sequence[complex]:
        """Convert ``text`` to a complex vector of length 128."""
        data = text.encode("utf-8")[:128]
        vec = [complex(b / 255.0, b / 255.0) for b in data]
        if len(vec) < 128:
            vec.extend([0j] * (128 - len(vec)))
        return vec

    def process_outward(self, grid: np.ndarray) -> str:
        """Translate a grid back into a UTF-8 string."""
        flat = np.asarray(grid).ravel()[:128]
        values = [int(max(0, min(255, round(abs(float(z.real)) * 255)))) for z in flat]
        return bytes(values).decode("utf-8", errors="ignore")

    @staticmethod
    def _coherence(text: str) -> float:
        words = text.split()
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    @staticmethod
    def _relevance(source: str, generated: str) -> float:
        src = set(source.split())
        gen = set(generated.split())
        if not src or not gen:
            return 0.0
        return len(src & gen) / len(src | gen)

    def _load_training_data(
        self,
    ) -> tuple[torch.Tensor, torch.Tensor] | tuple[None, None]:
        if nn is None:
            return None, None
        metrics = db_storage.fetch_benchmarks(limit=50, db_path=self._db_path)
        interactions = db_storage.fetch_interactions(limit=50, db_path=self._db_path)
        n = min(len(metrics), len(interactions))
        if n <= self._seq_len:
            return None, None
        metrics = list(reversed(metrics[:n]))
        interactions = list(reversed(interactions[:n]))

        model_to_idx = {"glm": 0, "deepseek": 1, "mistral": 2, "gate": 0}
        seqs: List[List[List[float]]] = []
        labels: List[int] = []
        for i in range(self._seq_len, n):
            seq: List[List[float]] = []
            for j in range(i - self._seq_len, i):
                m = metrics[j]
                length = len(interactions[j]["transcript"])
                seq.append(
                    [m["response_time"], m["coherence"], m["relevance"], float(length)]
                )
            seqs.append(seq)
            labels.append(model_to_idx.get(metrics[i]["model"], 0))

        x = torch.tensor(seqs, dtype=torch.float32)
        y = torch.tensor(labels, dtype=torch.long)
        return x, y

    def _train_predictor(self) -> None:
        if self._predictor is None or nn is None:
            return
        data = self._load_training_data()
        if data == (None, None):
            return
        x, y = data  # type: ignore
        dataset = torch.utils.data.TensorDataset(x, y)
        loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=True)
        opt = torch.optim.Adam(self._predictor.parameters(), lr=0.01)
        loss_fn = nn.CrossEntropyLoss()
        for _ in range(20):  # pragma: no cover - small training loop
            for xb, yb in loader:
                opt.zero_grad()
                loss = loss_fn(self._predictor(xb), yb)
                loss.backward()
                opt.step()

        self._train_x = x
        self._train_y = y

    def _optimize_parameters(self) -> None:
        if self._predictor is None or nn is None or not hasattr(self, "_train_x"):
            return
        pop = [np.random.rand(3) for _ in range(6)]
        loss_fn = nn.CrossEntropyLoss()
        for _ in range(5):  # pragma: no cover - short GA loop
            fitness = []
            for w in pop:
                logits = self._predictor(self._train_x) * torch.tensor(
                    w, dtype=torch.float32
                )
                loss = loss_fn(logits, self._train_y)
                fitness.append(-loss.item())
            ranked = [
                w
                for _, w in sorted(zip(fitness, pop), key=lambda t: t[0], reverse=True)
            ]
            parents = ranked[:2]
            pop = parents + [
                np.clip((parents[0] + parents[1]) / 2 + np.random.randn(3) * 0.1, 0, 2)
                for _ in range(4)
            ]
        self._selection_weights = ranked[0]

    def predict_best_llm(self) -> str:
        if self._predictor is None or nn is None or len(self._context) < self._seq_len:
            return "glm"
        seq = torch.tensor([list(self._context)[-self._seq_len :]], dtype=torch.float32)
        with torch.no_grad():
            logits = self._predictor(seq)[0] * torch.tensor(
                self._selection_weights, dtype=torch.float32
            )
            idx = int(torch.argmax(logits))
        mapping = {0: "glm", 1: "deepseek", 2: "mistral"}
        return mapping.get(idx, "glm")

    def benchmark(self, text: str) -> dict:
        start = perf_counter()
        vec = self.process_inward(text)
        out = self.process_outward(np.asarray(vec))
        elapsed = perf_counter() - start
        coh = self._coherence(out)
        rel = self._relevance(text, out)
        db_storage.log_benchmark("gate", elapsed, coh, rel, db_path=self._db_path)
        self._context.append([elapsed, coh, rel, float(len(text))])
        return {
            "vector": vec,
            "out_text": out,
            "response_time": elapsed,
            "coherence": coh,
            "relevance": rel,
        }


__all__ = ["GateOrchestrator"]
