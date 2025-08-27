# RAZAR Agent

The RAZAR runtime manager prepares a dedicated Python environment and starts
system components in priority order. It is invoked automatically by
`start_dev_agents.py` and `launch_servants.sh`, but it can also be run
stand‑alone for experimentation.

## Configuration

Components and optional dependencies are defined in `config/razar_config.yaml`:

```yaml
dependencies:
  - pyyaml
components:
  - name: memory_store
    command: "echo 'starting memory_store'"
    priority: 1
  - name: chat_gateway
    command: "echo 'starting chat_gateway'"
    priority: 2
```

`dependencies` lists packages installed into the virtual environment before any
components are launched. Each component is launched in ascending priority. The
manager records the last successful component in a `.state` file so that
subsequent runs resume from that point if a failure occurs.

## Usage

Run the manager directly:

```bash
python -m agents.razar.runtime_manager config/razar_config.yaml
```

The virtual environment is created next to the configuration file in a
`.razar_venv` directory.

Both `start_dev_agents.py` and `launch_servants.sh` invoke the manager before
launching their own services. Override the configuration path by setting the
`RAZAR_CONFIG` environment variable.
