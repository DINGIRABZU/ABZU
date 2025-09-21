# Vector DB Scaling Checklist

This checklist tracks the performance validation required by the roadmap's
Memory Fabric milestones. Metrics were produced from a simulated 10k-item
corpus using the benchmarking utilities in
`scripts/run_vector_memory_scaling.py` and recorded in
`data/vector_memory_scaling/latency_metrics.json`.

> Chroma fixtures are generated on demand. Run
> `python scripts/ingest_ethics.py --emit-seed --seed-output data/vector_memory_scaling/chroma_seed`
> before collecting new metrics to refresh the manifest and SQLite dump.

| Item | Status | Evidence |
| --- | --- | --- |
| Simulate a 10k-item corpus and execute the vector memory ingestion workflow. | ✅ | `scripts/run_vector_memory_scaling.py` populates `data/vector_memory_scaling/corpus.jsonl` and logs timings while ingesting all 10k entries. |
| Capture P95 latency for writes and queries in each storage mode (standard and fallback). | ✅ | Metrics stored in `data/vector_memory_scaling/latency_metrics.json` (P95 write/query latencies per mode). |
| Confirm Memory Fabric targets (P95 ≤ 120 ms for queries on 10k items). | ✅ | `memory_store_fallback` query P95 = 2.47 ms; `vector_memory` query P95 = 32.3 ms. |
| Automate validation to rerun representative queries and ensure thresholds hold. | ✅ | `tests/test_vector_memory_scaling.py` replays sampled queries against both storage modes and asserts the recorded P95 latencies remain within targets. |

## Latest Metrics Snapshot

| Mode | Write P95 (s) | Query P95 (s) | Duration (s) |
| --- | --- | --- | --- |
| `vector_memory` | 0.01969 | 0.03225 | 84.26 |
| `memory_store_fallback` | 0.01316 | 0.00247 | 78.46 |

> The fallback path now leverages NumPy-accelerated distance calculations for
> search, delivering sub-3 ms P95 queries while maintaining rapid writes. The
> FAISS-backed primary path continues to provide consistent millisecond-level
> reads. Both modes comfortably satisfy the ≤ 0.120 s P95 requirement for the
> 10k-item corpus.
