# Benchmarks

Run `make bench` to execute all benchmarks. Results are written to `data/benchmarks`.

## Baseline metrics

| Benchmark | Metric | Value |
| --- | --- | --- |
| Memory store insertion | adds/sec | 26,769.82 |
| Memory store search | seconds | 0.0078 |
| Chat gateway routing | messages/sec | 1,122,012.08 |
| LLM throughput | tokens/sec | 4,077.48 |

## Rust vs Python path

Run `python rust_vs_python_path.py` to compare call throughput between the
Rust `neoabzu_chakrapulse` crate and a legacy Python implementation. Typical
results on a development machine:

| Path | Calls/sec |
| --- | --- |
| Rust emit | 1,200,000 |
| Python emit | 350,000 |
