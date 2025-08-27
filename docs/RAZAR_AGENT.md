# RAZAR Agent Environment

This document describes how to build the Python environment for the RAZAR components.

## Building the environment

`razar/environment_builder.py` manages creation of a virtual environment and installs
packages for each component layer defined in `razar_env.yaml`.

```bash
python razar/environment_builder.py --venv .razar_venv
```

The script ensures a compatible Python version, creates the virtual environment and
installs dependencies layer by layer.

## Configuration

Dependencies are declared in `razar_env.yaml` under the `layers` key. Each entry maps a
layer name to a list of packages:

```yaml
layers:
  razar:
    - pyyaml
  inanna:
    - requests
  crown:
    - numpy
```

Add or modify packages as required by updating this file and re-running the builder.

## Health Checks

RAZAR probes each component through `agents/razar/health_checks.py` after a
startup command succeeds.  Service‑specific functions can examine logs or
metrics and return `True` when the component is healthy.  For the Vision
Adapter (YOLOE), a check might confirm that prediction FPS stays above a target
threshold.  Failed checks automatically quarantine the component via
`quarantine_manager.py`, preventing unstable services from continuing in the
boot sequence.

## Runtime Manager

`agents/razar/runtime_manager.py` boots the configured components in order of
their priority. On first run it builds a dedicated virtual environment and
installs the packages declared for each component in `razar_env.yaml`.  The
manager tracks progress so interrupted boots can resume where they left off and
quarantines modules that fail to start or pass a health check.

Launch the sequence by providing the path to `razar_config.yaml`:

```bash
python agents/razar/runtime_manager.py config/razar_config.yaml
```

Each component entry in the configuration specifies a `command` and `priority`.
After every successful start the manager records the component name in
`logs/razar_state.json`, allowing subsequent runs to skip completed steps.
If a component fails, its metadata is moved to the `quarantine/` directory and
an entry is appended to `docs/quarantine_log.md`.

### Recovery

1. **Resume** – rerun the manager; it continues after the last healthy step
   recorded in `logs/razar_state.json`.
2. **Full restart** – remove `logs/razar_state.json` and rerun the manager to
   rebuild the stack from the first component.
3. **Quarantine review** – inspect `quarantine/` and
   `docs/quarantine_log.md` for details on failed modules. Resolve issues, then
   remove the component's JSON file and rerun to retry.

## Prioritized Test Execution

Tests can be executed in priority tiers using
`agents/razar/pytest_runner.py`. The mapping of test files to tiers is stored in
`tests/priority_map.yaml` with levels `P1` through `P5`.

The runner executes one tier at a time using the `pytest-order` plugin so that
high‑priority smoke tests fail fast. After any failure the runner records the
failing test node and tier in `logs/pytest_last_failed.json`. Subsequent runs
with `--resume` continue from that point.

Run all tests in order of priority:

```bash
python agents/razar/pytest_runner.py
```

Execute only selected tiers (for example P1 and P2):

```bash
python agents/razar/pytest_runner.py --priority P1 P2
```

Resume from the last failing test session:

```bash
python agents/razar/pytest_runner.py --resume
```

Output from each invocation is appended to `logs/pytest_priority.log` for
inspection by other RAZAR components.

## Automated Code Repair

`agents/razar/code_repair.py` automates patching of failing modules. The helper
collects the failing source and error message, queries the CROWN LLM (or fallback
models) for a patch suggestion and evaluates the result in a sandbox:

1. **Context gathering** – read the module source and failing test output.
2. **Patch request** – submit the context to `GLMIntegration` or alternate
   models for a code fix.
3. **Sandbox tests** – write the patched module to a temporary directory and
   execute the module's test files with `pytest` using that sandbox on the
   `PYTHONPATH`.
4. **Reactivation** – if tests succeed, copy the patched file back to the
   repository and reintroduce the module via `quarantine_manager.reactivate_component`.

This workflow allows RAZAR to iteratively heal quarantined components without
manually editing the repository.
