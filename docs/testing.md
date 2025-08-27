# Testing

```mermaid
flowchart LR
    D[Developer] --> T[pytest]
    T --> R[Report]
```

## Manual smoke tests

### Prioritized test tiers

Execute tests in priority order using the RAZAR runner. The mapping of test
files to tiers lives in `tests/priority_map.yaml`.

Run all tiers:

```bash
python agents/razar/pytest_runner.py
```

Resume from the last failing tier:

```bash
python agents/razar/pytest_runner.py --resume
```

### CLI console interface

1. From the repository root, run `python -m cli.console_interface`.
1. Confirm that an interactive prompt (e.g., `INANNA>`) appears and accepts input.
1. Exit with `Ctrl+C` when finished.

### Avatar console

1. Run `bash start_avatar_console.sh`.
   - Ensure `start_crown_console.sh` is executable or invoke it with `bash`.
1. Wait for WebRTC initialization messages in the logs and verify that a video feed is displayed.
1. Use `Ctrl+C` to terminate the services.

## Notes

- During this test run, the CLI setup encountered dependency initialization issues, preventing the prompt from appearing.
- `start_avatar_console.sh` reported a permission error for `start_crown_console.sh` and the WebRTC video stream did not start.

## Common test failure modes

- Missing pytest plugins such as `pytest-cov` will cause command-line options errors. Install required dev dependencies.
- Duplicate or conflicting test module names can trigger collection errors like "import file mismatch". Remove `__pycache__` files or rename tests to be unique.
- ImportError during test collection often indicates missing runtime dependencies or incorrect module paths. Verify imports such as `core.load_config` exist or adjust `PYTHONPATH`.
