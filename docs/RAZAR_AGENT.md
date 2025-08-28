# RAZAR Runtime Manager

The **RAZAR** runtime manager prepares a lightweight environment for service
components and launches them in a defined priority order. It ensures that each
component's dependencies are installed in an isolated virtual environment and
records progress so failed launches can resume from the last healthy component.

## Environment Setup

Dependencies for each component layer are listed in `razar_env.yaml`. When
RAZAR runs it will:

1. Create a virtual environment under `.razar_venv` if one does not already
   exist.
2. Install packages required by the targeted components.
3. Update `PATH` and `VIRTUAL_ENV` so launched subprocesses inherit the
   environment.

The last successfully started component is written to
`logs/razar_state.json`. This allows subsequent runs to resume from the point of
failure rather than starting from scratch.

## Quarantine Handling

If a component fails to start or does not pass its health check, RAZAR invokes
`agents.razar.quarantine_manager` to quarantine the component and its module
path. Quarantined components are skipped on future runs.

## Usage

The runtime manager can be invoked directly:

```bash
python -m agents.razar.runtime_manager config/razar_config.yaml
```

`start_dev_agents.py` and `launch_servants.sh` call RAZAR before performing
other work. You can override the configuration file by setting
`RAZAR_CONFIG` in the environment.
