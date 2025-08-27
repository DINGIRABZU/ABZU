from __future__ import annotations

"""Run all benchmark scripts and report their metrics."""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
sys.path.append(str(Path(__file__).resolve().parent.parent))

from chat_gateway_benchmark import benchmark_chat_gateway
from llm_throughput_benchmark import benchmark_llm
from memory_store_benchmark import benchmark_memory_store


def main() -> None:
    results = {
        "memory_store": benchmark_memory_store(),
        "chat_gateway": benchmark_chat_gateway(),
        "llm_throughput": benchmark_llm(),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
