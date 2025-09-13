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
