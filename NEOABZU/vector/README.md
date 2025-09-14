# neoabzu-vector

Rust vector operations for Neo-ABZU.

## Usage

- **Run tests** with the default feature set (links against `libpython` and enables `pyo3/auto-initialize`):
  ```bash
  cargo test
  ```
- **Build the Python extension module** by disabling default features and enabling `python-extension`:
  ```bash
  cargo build --release --no-default-features --features python-extension
  ```

- **Serve gRPC endpoints** over Tonic:
  ```bash
  export NEOABZU_VECTOR_STORE=tests/data/store.json
  cargo run -p neoabzu-vector --bin server
  ```
  The server embeds each string in the JSON array and exposes `Init` and
  `Search` RPCs on `0.0.0.0:50051`.

- **Call from Python** using the bundled helpers:
  ```python
  from neoabzu.vector import VectorClient

  with VectorClient("http://localhost:50051") as client:
      client.init()
      results = client.search("hello", 2)
  ```
