# Memory Query Benchmark Report

This report summarizes the performance of concurrent searches across the cortex, vector, and spiral memory layers.

## Method

`benchmarks/query_memory_bench.py` issues multiple `query_memory` calls in parallel using a thread pool. Each query measures the time to retrieve results across layers.

## Sample Results

| Query | Duration (s) |
|---|---|
| alpha | 0.0102 |
| gamma | 0.0094 |
| beta  | 0.0109 |
| delta | 0.0085 |
| epsilon | 0.0026 |

The full dataset is stored in [`data/benchmarks/query_memory.csv`](../../data/benchmarks/query_memory.csv) for downstream analysis.

Run the benchmark locally with:

```
python benchmarks/query_memory_bench.py
```

Benchmarks also run in CI via the manually-triggered `Benchmarks` workflow.
