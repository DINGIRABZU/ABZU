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
