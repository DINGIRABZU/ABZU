import argparse
import time

from neoabzu_chakrapulse import emit_pulse as rust_emit


def python_emit(source: str, ok: bool) -> None:
    return {"source": source, "ok": ok}


def benchmark(func, iterations: int) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        func("bench", True)
    end = time.perf_counter()
    return iterations / (end - start)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Rust vs Python paths")
    parser.add_argument("--iterations", type=int, default=10000)
    args = parser.parse_args()
    rust_rate = benchmark(rust_emit, args.iterations)
    py_rate = benchmark(python_emit, args.iterations)
    print(f"Rust emit: {rust_rate:.2f} calls/sec")
    print(f"Python emit: {py_rate:.2f} calls/sec")


if __name__ == "__main__":
    main()
