# Contributing

To run the test suite you need a few Python packages:

- `numpy`
- `scipy`
- `soundfile`
- `librosa`
- `pytest`

Install them with:

```bash
pip install -r dev-requirements.txt
```

You can also run the helper script which prints a brief warning about the
download size:

```bash
./scripts/install_test_deps.sh
```

## Dependency lock file

Runtime dependencies are pinned in `requirements.lock` which is generated from
`pyproject.toml`.

After modifying dependencies, refresh the lock file and commit the result:

```bash
uv pip compile --no-deps pyproject.toml -o requirements.lock
```

