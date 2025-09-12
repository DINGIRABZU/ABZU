import argparse
import importlib
import time


def measure(
    module_name: str, func_name: str, arg: str, iterations: int = 1000
) -> float:
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    start = time.perf_counter()
    for _ in range(iterations):
        func(arg)
    end = time.perf_counter()
    return (end - start) / iterations


def main():
    parser = argparse.ArgumentParser(description="Measure PyO3 call latency")
    parser.add_argument("--module", default="neoabzu_core")
    parser.add_argument("--function", default="evaluate")
    parser.add_argument("--arg", default="(\\x.x)y")
    parser.add_argument("--iterations", type=int, default=1000)
    args = parser.parse_args()
    avg = measure(args.module, args.function, args.arg, args.iterations)
    print(f"Average call latency for {args.module}.{args.function}: {avg * 1e6:.2f} µs")


if __name__ == "__main__":
    main()
