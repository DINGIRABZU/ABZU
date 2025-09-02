"""Benchmark message routing through the chat gateway."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import types

api_stub = types.ModuleType("api")
api_stub.server = types.SimpleNamespace(
    generate_video=lambda *args, **kwargs: None,
    broadcast_avatar_update=lambda *args, **kwargs: None,
    list_styles=lambda *args, **kwargs: None,
)
sys.modules["api"] = api_stub

from communication.gateway import Gateway, ChannelMessage


class DummyCore:
    async def handle_message(self, message: ChannelMessage) -> None:
        return None


async def _bench(messages: int = 1000) -> dict[str, float]:
    core = DummyCore()
    gateway = Gateway(core)

    start = time.perf_counter()
    for _ in range(messages):
        await gateway.handle_incoming("chat", "user", "hello")
    duration = time.perf_counter() - start

    metrics = {"messages_per_sec": round(messages / duration if duration else 0.0, 2)}
    out_dir = Path("data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "chat_gateway.json"
    out_file.write_text(json.dumps(metrics))
    return metrics


def benchmark_chat_gateway(messages: int = 1000) -> dict[str, float]:
    """Public wrapper that runs the asynchronous benchmark."""
    return asyncio.run(_bench(messages))


def main() -> None:
    metrics = benchmark_chat_gateway()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
