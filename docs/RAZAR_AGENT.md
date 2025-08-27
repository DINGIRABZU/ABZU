# RAZAR Runtime Manager

`RuntimeManager` coordinates the startup of RAZAR components. It ensures a
Python virtual environment exists, launches components in order of their
priority and records the last successful component so a failed run can resume
from that point.

## Configuration

Components and their priorities are defined in a YAML file. An example lives at
`config/razar_config.yaml`:

```yaml
components:
  - name: example
    priority: 1
    command: "echo 'RAZAR component running'"
```

Each entry lists a component name, numeric priority (lower values start first)
and the shell command used to launch it.

## Usage

Run the manager by pointing it at the configuration file:

```bash
python -m agents.razar.runtime_manager config/razar_config.yaml
```

On failure, the manager writes the last successful component to a `.state` file
next to the configuration. Re‑running the command starts from the component
following that entry.
