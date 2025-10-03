# Memory Module Contract

## Overview
The memory contract covers the lightweight SQLite-backed `MemoryStore`, the vector snapshot helper, and the shims that stand in for Chroma/Neo‑ABZU services during sandbox runs. It documents how ingestion, similarity search, and snapshot export behave when optional accelerators are absent.

## Sample Inputs and Outputs
- **Scalar vector ingestion.** Tests add two vectors with IDs `"a"` and `"b"` and later query for the nearest neighbours with a 2D query vector. The store returns tuples `(id, score, metadata)` where the expected IDs include both inserted records before deletion.【F:tests/memory/test_memory_store_fallback.py†L6-L17】
- **Snapshot manifest.** The vector memory snapshotter persists files under `<db_path>/snapshots/` and lists each snapshot path inside `manifest.json`. After restoring the latest snapshot, `query_vectors(limit=10)` returns entries whose `text` field matches the stored payload.【F:tests/memory/test_vector_memory.py†L24-L47】
- **Baseline embeddings.** The `FakeCollection` fixture accepts both single-record and batched `add` calls, tracking inserted embeddings and metadata, while `query` returns ordered matches shaped like the real Chroma responses (`{"ids": [[...]], "metadatas": [[...]]}`).【F:tests/fixtures/chroma_baseline/fake_chroma.py†L15-L156】
- **Stage readiness metrics.** Memory readiness bundles emit rotation and heartbeat metadata such as `rotation_summary` and `heartbeat_expiry`, which downstream automation consumes to gate releases.【F:tests/fixtures/stage_readiness/stage_b/20240102T000000Z-stage_b1_memory_proof/summary.json†L1-L16】

## Expected Logging and Telemetry
- Memory readiness exports should surface rotation summaries and heartbeat expirations that match the Stage B fixtures above, signalling when credential windows need renewal.【F:tests/fixtures/stage_readiness/stage_b/20240102T000000Z-stage_b1_memory_proof/summary.json†L1-L16】
- Sandbox automation emits `EnvironmentLimitedWarning` entries when native extensions are unavailable; the runtime loader keeps a list of forced modules (including `neoapsu_memory`) to patch in stubs before tests execute.【F:scripts/_stage_runtime.py†L27-L63】

## Failure Modes and Recovery
- **Optional dependency gaps.** When FAISS and NumPy are unavailable, the store falls back to pure-Python similarity scoring while keeping CRUD semantics intact. Tests verify this by monkeypatching both dependencies to `None` and ensuring search/delete still succeed.【F:tests/memory/test_memory_store_fallback.py†L6-L17】
- **Snapshot drift.** If snapshot manifests are missing, re-running `persist_snapshot()` repopulates the manifest before the next restore attempt. Reuse the snapshot scaffolding from `tests/memory/test_vector_memory.py` when reproducing recovery flows.【F:tests/memory/test_vector_memory.py†L24-L47】

## Reusable Fixtures and Stubs
- Import `FakeCollection` from `tests/fixtures/chroma_baseline/fake_chroma.py` for deterministic vector-store behaviour in contract tests.【F:tests/fixtures/chroma_baseline/fake_chroma.py†L15-L156】
- Seed readiness telemetry by copying the Stage B `summary.json` template in `tests/fixtures/stage_readiness/` so log parsers keep consuming identical keys.【F:tests/fixtures/stage_readiness/stage_b/20240102T000000Z-stage_b1_memory_proof/summary.json†L1-L16】
- Use the sandbox override registry from `_stage_runtime` to stub heavy dependencies (`neoapsu_memory`, `crown_decider`) while keeping interfaces identical across Python and native builds.【F:scripts/_stage_runtime.py†L27-L108】

## Future Work
Hardware parity requires swapping the SQLite shim with the `neoabzu_memory::MemoryBundle` and replaying Stage B rotations plus Stage C readiness hashes on gate-runner hardware before promoting the Rust bundle.【F:docs/roadmap.md†L191-L192】 Continue publishing checksum and telemetry parity to Grafana once hardware spans are available, mirroring the roadmap checkpoints so reviewers can trace sandbox evidence through Stage G and GA cutovers.【F:docs/roadmap.md†L170-L218】 Until FFmpeg/SoX are restored in the sandbox, keep documenting `EnvironmentLimitedWarning` skips alongside the memory contract results for audit parity.【F:scripts/_stage_runtime.py†L27-L63】
