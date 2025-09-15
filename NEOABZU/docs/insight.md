# Insight Engine

`neoabzu_insight` exposes the reasoning utilities that the Crown Router uses for
lightweight embeddings and semantic probes.

## Crown bridge

The crate ships a PyO3 hook named `crown_semantic` that defers to the
`neoabzu_crown` Python module. When the Crown Router is available the bridge
invokes its `insight_semantic` binding and returns the response as a Rust
`Vec<(String, f32)>`. If the module is absent, it falls back to the local
`semantics` helper so insight calls still succeed during standalone usage.

```python
import neoabzu_insight

neoabzu_insight.crown_semantic("welcome home")
```

The same bridge is exported to Rust so subsystems that already hold the Python
GIL can forward requests without reimplementing the Crown logic.
