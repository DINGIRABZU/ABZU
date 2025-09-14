"""Simple load test for the vector gRPC service."""

import json
import os
import socket
import subprocess
import time
from pathlib import Path

import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from neoabzu.vector import VectorClient


def wait_port(host: str, port: int, timeout: float = 1.0, retries: int = 60) -> None:
    for _ in range(retries):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return
        except OSError:
            time.sleep(1)
    raise RuntimeError("server did not start")


def main() -> None:
    store = root / "vector" / "tests" / "data" / "store.json"
    if not store.exists():
        store.parent.mkdir(parents=True, exist_ok=True)
        json.dump(["alpha", "beta"], store.open("w"))
    env = os.environ.copy()
    env["NEOABZU_VECTOR_STORE"] = str(store)
    server = subprocess.Popen(
        ["cargo", "run", "-p", "neoabzu-vector", "--bin", "server"],
        cwd=root,
        env=env,
    )
    try:
        wait_port("localhost", 50051)
        with VectorClient("http://localhost:50051") as client:
            client.init()
            start = time.time()
            for _ in range(50):
                client.search("alpha", 1)
            dur = time.time() - start
            print(f"50 searches in {dur:.2f}s -> {50/dur:.2f} req/s")
    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    main()
