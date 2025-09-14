# neoabzu-rag

Retrieval-augmented generation components for Neo-ABZU.

The Rust module mirrors the Python `rag.orchestrator` API.  `retrieve_top`
performs hybrid retrieval across in-memory context and any external
connectors, yielding a ranked set of results.

## Usage

- **Run tests** with default features (links against `libpython` and enables `pyo3/auto-initialize`):
  ```bash
  cargo test
  ```
- **Build the Python extension module** by disabling default features and enabling `python-extension`:
  ```bash
  cargo build --release --no-default-features --features python-extension
  ```
