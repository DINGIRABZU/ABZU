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
their priority. The manager creates a virtual environment on first run,
installs any listed dependencies and tracks progress so that interrupted boots
can resume where they left off.

Launch the sequence by providing the path to `razar_config.yaml`:

```bash
python agents/razar/runtime_manager.py config/razar_config.yaml
```

Each component entry in the configuration specifies a `command` and `priority`.
After every successful start the manager records the component name in
`logs/razar_state.json`, allowing subsequent runs to skip completed steps.

## Prioritized Test Execution

Tests can be executed in priority tiers using `agents/razar/pytest_runner.py`.
The mapping of test files to tiers is stored in `tests/priority_map.yaml` with
levels `P1` through `P5`.

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

Output from each invocation is written to `logs/pytest_priority.log` for
inspection by other RAZAR components.
