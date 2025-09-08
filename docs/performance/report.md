# Memory Query Benchmark Report

This report summarizes the performance of concurrent searches across the cortex,
vector, and spiral memory layers as part of the load-testing suite.

## Method

`benchmarks/query_memory_bench.py` issues multiple `query_memory` calls in parallel using a thread pool. Each query measures the time to retrieve results across layers while aggregate throughput and latency are recorded.

## Sample Results

| Query | Duration (s) |
|---|---|
| alpha | 0.0069 |
| beta  | 0.0064 |
| gamma | 0.0055 |
| delta | 0.0050 |
| epsilon | 0.0010 |

**Throughput:** 307.99 queries/sec  
**Average latency:** 0.0050 s

The full dataset is stored in [`data/benchmarks/query_memory.csv`](../../data/benchmarks/query_memory.csv) and aggregated metrics in [`data/benchmarks/query_memory.json`](../../data/benchmarks/query_memory.json) for downstream analysis.

Run the benchmark locally with:

```
make bench-query-memory
```

Benchmarks run weekly via the scheduled `Benchmarks` GitHub Actions workflow.
