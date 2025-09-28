# neoabzu-memory

Neo-ABZU memory primitives.

## Usage

- **Run tests** with default features (links against `libpython` and enables `pyo3/auto-initialize`):
  ```bash
  cargo test
  ```
- **Build the Python extension module** by disabling default features and enabling `python-extension`:
  ```bash
  cargo build --release --no-default-features --features python-extension
  ```

## Stage B readiness checklist

- **Refresh sample data** before running the Stage B load proof. Execute the bootstrap utility so `data/cortex_memory_spiral.jsonl`, `data/emotions.db`, `data/story.log`, and companion indices contain fresh records:
  ```bash
  PYTHONPATH=. EMOTION_DB_PATH=data/emotions.db \
    python scripts/init_memory_layers.py
  ```
  The cortex shard must expose at least one record tagged `example`; otherwise `scripts/check_memory_layers.py` reports `RuntimeError: cortex layer empty` and the load proof aborts the pretest.
- **Inject a fresh emotional reading** immediately before invoking any health check. The probe reads the prior 60 seconds from `data/emotions.db`, so log at least one vector tied to the Stage B fixture path:
  ```bash
  EMOTION_DB_PATH=data/emotions.db PYTHONPATH=. \
    python -c "from memory.emotional import log_emotion; log_emotion([0.42])"
  ```
  Skipping this step leaves the emotional layer empty and `scripts/check_memory_layers.py` raises `RuntimeError: emotional layer empty` even though the database exists.
- **Compile the native bundles** so `neoabzu_memory` and `neoabzu_core` import without stubs. Build both crates in release mode (no default features) and expose the resulting shared libraries on `sys.path`:
  ```bash
  cargo build -p neoabzu-memory --release --no-default-features --features python-extension --lib
  (cd NEOABZU/core && cargo build --release)
  ```
  `scripts/_stage_runtime.bootstrap()` discovers `target/release` outputs automatically; no manual `sys.path` edits are required once the artifacts exist.
- **Verify the Python runtime sees the freshly built bundles** after a clean checkout or `cargo clean` run. `scripts/check_memory_layers.py` and the load proof default to the native `neoabzu_memory` bundle; if the shared objects are missing they fall back to `memory.optional.neoabzu_bundle`, marking every layer as `skipped`.
- **Verify the health check** immediately after refreshing the fixtures:
  ```bash
  PYTHONPATH=. EMOTION_DB_PATH=data/emotions.db \
    python scripts/check_memory_layers.py
  ```
  A passing run prints `memory checks passed` and confirms that the cortex, emotional, spiritual, narrative, and optional mental fallbacks all return data.
