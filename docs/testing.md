# Testing

```mermaid
flowchart LR
    D[Developer] --> T[pytest]
    T --> R[Report]
```

## Testing Workflow

1. Run formatting and static checks for the files you touched:

   ```bash
   pre-commit run --files <changed_files>
   ```

2. Execute the full test suite with coverage enabled:

   ```bash
   pytest --cov
   coverage report
   coverage-badge -o coverage.svg
   ```

3. Maintain a **minimum 85% repository coverage** and aim for **≥90%** on
   modified modules. Update `component_index.json` when coverage metrics change.

4. On failures or drops below thresholds:

   - Inspect `logs/pytest_priority.log` and `logs/razar.log` for details.
   - Rerun the failing tier with `--maxfail=1` for rapid feedback.
   - Isolate recurring failures using `python -m razar.quarantine_manager
     quarantine <component>` and consult [diagnostics.md](diagnostics.md).
   - Escalate unresolved issues following
     [co_creation_escalation.md](co_creation_escalation.md).

## Required pytest plugins

The test suite expects certain plugins to be available:

- `pytest-cov` for coverage reporting via the `--cov` options in `pytest.ini`.

Install them with `pip install -r dev-requirements.txt`.

The project uses a `src` layout. Install the repository in editable mode or
prepend the source path when running tests to avoid import errors:

```bash
pip install -e .
# or
PYTHONPATH=src pytest
```

## Handling interactive prompts

Some modules expose command line chat loops that wait for `input()`.
For automated tests, supply predetermined prompts or mock `input` so
tests do not hang.  The `inanna_ai` CLI accepts a `prompts` iterable:

```python
from INANNA_AI_AGENT import inanna_ai
inanna_ai.main(["chat"], prompts=["hello", "exit"])
```

Other interactive entry points should be skipped or patched similarly.

## Manual smoke tests

### Prioritized test tiers

Execute tests in priority order using the RAZAR runner. The mapping of test
files to tiers lives in `tests/priority_map.yaml`. Tiers run sequentially so
critical smoke tests fail fast. Progress is persisted to `logs/pytest_state.json`
so subsequent runs with `--resume` continue from the last failing test. Output
from every run appends to `logs/pytest_priority.log`.  A minimal mapping looks
like and can be expanded to include tiers `P3`–`P5`:

```yaml
P1:
  - tests/test_smoke_imports.py
  - tests/test_core_scipy_smoke.py
P2:
  - tests/test_server.py
  - tests/test_api_endpoints.py
P3:
  - tests/test_learning.py
  - tests/test_voice_config.py
P4:
  - tests/test_music_generation.py
  - tests/test_dashboard_app.py
P5:
  - tests/test_orchestrator.py
  - tests/test_rag_engine.py
```

Run all tiers:

```bash
python agents/razar/pytest_runner.py
```

Run a specific tier:

```bash
python agents/razar/pytest_runner.py --priority P1
```

Resume from the last failing test:

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
- Repeated failures tied to a specific service cause RAZAR to quarantine the component and skip dependent tests. Review `logs/razar.log` and [`quarantine_log.md`](quarantine_log.md) for details and run the scripts in [diagnostics.md](diagnostics.md) before retrying.

### Quarantine and Diagnostics
Use RAZAR's quarantine manager to isolate components that consistently fail:

```bash
python -m razar.quarantine_manager quarantine <component>
```

The component's metadata moves to `quarantine/` and an entry records the action in [`quarantine_log.md`](quarantine_log.md). Employ the utilities listed in [diagnostics.md](diagnostics.md) to analyze missing dependencies or corrupted state. Once resolved, follow the [Recovery Playbook](recovery_playbook.md) to restore service and consult [developer_onboarding.md](developer_onboarding.md) for environment rebuild tips.
