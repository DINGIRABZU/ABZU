# Test suite notes

## Chakra and component organization

Tests are annotated with `chakra` and `component` markers derived from
`component_index.json`. Use `pytest -m "chakra('heart')"` to run Heart layer
tests or filter by component with `pytest -m "component('bana')"`. Directory
structure remains available for broad organization, but markers provide the
canonical grouping.

## Hugging Face hub stub

The test configuration injects a lightweight stub of the
[`huggingface_hub`](https://github.com/huggingface/huggingface_hub) package. The
stub lives at `src/spiral_os/_hf_stub.py` and defines no-op
`snapshot_download` and `HfHubHTTPError` symbols. During tests,
`tests/conftest.py` registers this stub in `sys.modules` so modules can import
`huggingface_hub` without installing the real dependency or performing network
operations.
