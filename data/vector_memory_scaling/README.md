# Vector Memory Scaling Fixtures

The benchmarking utilities generate their fixtures on demand. To rebuild the
Chroma seed used during scaling drills run:

```bash
python scripts/ingest_ethics.py --emit-seed --seed-output data/vector_memory_scaling/chroma_seed
```

The command reindexes the Markdown sources in `sacred_inputs/`, copies the
resulting `data/chroma/` payload into the provided directory, and emits a
`manifest.json` and `chroma.dump.sql` alongside the copied files. The scaling
harness reads those artefacts at runtime, so please **do not commit** the binary
output; only the manifest files are needed for verification.
