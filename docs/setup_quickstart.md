# Setup Quickstart

## Minimal Installation

1. Ensure Python 3.10 or later is available.
2. From the repository root, install the core runtime:
   ```bash
   pip install .
   ```
3. For mental-model features backed by Neo4j, include the optional extras:
   ```bash
   pip install .[mental]
   ```

## World Creation

After installation, bootstrap the default world:

```bash
abzu-bootstrap-world
```

The command wraps `scripts/bootstrap_world.py`, which prepares file-backed memory stores under `data/`, initializes mandatory layers, and prints the status for each. Set `WORLD_NAME` to select a specific manifest; otherwise, the default manifest is used.

Run `abzu-bootstrap-world -h` for optional arguments and flags.
