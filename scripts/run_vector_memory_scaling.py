"""Run the vector memory scaling benchmark and persist latency metrics."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from monitoring.vector_memory_scaling import run_benchmark


def main() -> None:
    run_benchmark()


if __name__ == "__main__":
    main()
