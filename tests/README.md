# Test suite notes

## Chakra and component organization

Tests are organized under `tests/<chakra>/<component>/` and annotated with
`chakra` and `component` markers derived from `component_index.json`. Use
`pytest -m "chakra('heart')"` to run Heart layer tests or filter by component
with `pytest -m "component('bana')"`. The directory layout mirrors the
component index while markers provide the canonical grouping.

## Hugging Face hub stub

The test configuration injects a lightweight stub of the
[`huggingface_hub`](https://github.com/huggingface/huggingface_hub) package. The
stub lives at `src/spiral_os/_hf_stub.py` and defines no-op
`snapshot_download` and `HfHubHTTPError` symbols. During tests,
`tests/conftest.py` registers this stub in `sys.modules` so modules can import
`huggingface_hub` without installing the real dependency or performing network
operations.

## Chroma baseline fixture

Regression tests that exercise Chroma persistence use the deterministic fixture
in `tests/fixtures/chroma_baseline/`. The baseline data lives in
`baseline.json`, while `fake_chroma.py` exposes utilities for stubbing
`chromadb` and synthesising repeatable stores. The helpers are used throughout
the suite (for example in `tests/test_spiral_vector_db.py`) to verify both the
happy path and failure handling without tracking binary SQLite snapshots.

To regenerate the fixture, edit `baseline.json` with the desired records and
then run the helper to materialise a SQLite payload for manual inspection:

```bash
python - <<'PY'
from pathlib import Path
from tests.fixtures.chroma_baseline import materialize_sqlite

db_path = materialize_sqlite(Path('tests/fixtures/chroma_baseline/artifacts'))
print(db_path)
PY
```

Running `pytest tests/test_spiral_vector_db.py::test_materialize_sqlite_mirror`
after updating the JSON validates that the text fixture and SQLite mirror stay
in sync.
