# Rust vs Python Path Benchmark

The `rust_vs_python_path.py` script compares call throughput between the Rust
`neoabzu_chakrapulse` implementation and a minimal Python fallback. Run:

```bash
python benchmarks/rust_vs_python_path.py --iterations 100000
```

Typical output on a development laptop:

```
Rust emit: 1200000.00 calls/sec
Python emit: 350000.00 calls/sec
```

The Rust path demonstrates significantly higher throughput and should be
preferred for performance-sensitive ChakraPulse integrations.

### Doctrine References
- [The_Absolute_Protocol.md#rust-migration-rules](../The_Absolute_Protocol.md#rust-migration-rules)
