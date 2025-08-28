# RAZAR Agent

The **RAZAR Agent** ignites ABZU before any servant awakens. It establishes a
clean launch arena, manages isolated dependencies, and coordinates recovery when
components falter. RAZAR’s mission spans three roles:

- **Pre‑creation igniter** – validates prerequisites, compiles the ignition
  plan and lights the first spark for downstream agents.
- **Virtual‑environment manager** – builds the per‑component environment defined
  in `razar_env.yaml`, updates `PATH`/`VIRTUAL_ENV`, and records progress in
  `logs/razar_state.json` so restarts resume from the last healthy step.
- **Recovery coordinator** – performs health checks, quarantines failed modules
  via `agents.razar.quarantine_manager`, and restarts services after repairs.

## Usage

Invoke RAZAR directly to bootstrap components:

```bash
python -m agents.razar.runtime_manager config/razar_config.yaml
```

`start_dev_agents.py` and `launch_servants.sh` call RAZAR before performing
other work. Override the configuration file by setting `RAZAR_CONFIG` in the
environment.

## Remote Agent Pipeline

RAZAR can extend its capabilities at runtime by pulling helper agents from
remote locations. The :mod:`agents.razar.remote_loader` utility supports three
strategies:

1. **HTTP modules** – download a single Python file from an HTTP(S) endpoint,
   load it with ``importlib`` and execute its ``configure()`` and ``patch()``
   hooks.
2. **Git repositories** – clone a repository via **GitPython** and load a
   specified module path.
3. **HTTP GPT services** – interact with a JSON API exposing ``/configure`` and
   ``/patch`` routes using :mod:`requests`.

Each agent's configuration and any patch suggestions are recorded in
``logs/razar_remote_agents.json``. The ``patch_on_test_failure`` helper will
request a patch from a remote agent when tests fail, apply the returned diff in
a sandbox and re-run the test suite before committing the change.
