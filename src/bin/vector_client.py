#!/usr/bin/env python3
"""Command-line client for the NeoABZU vector service."""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "NEOABZU"))
from neoabzu.vector import VectorClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the NeoABZU vector service")
    parser.add_argument("text", help="query text")
    parser.add_argument("--top", type=int, default=5, help="number of results")
    parser.add_argument(
        "--addr", default="http://localhost:50051", help="service address"
    )
    args = parser.parse_args()

    with VectorClient(args.addr) as client:
        resp = client.search(args.text, args.top)
        for r in resp.results:
            print(f"{r.score:.3f}\t{r.text}")


if __name__ == "__main__":
    main()
