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

After installation, create and initialize a world with:

```bash
abzu-bootstrap-world
```

The command prepares local file-backed memory stores under `data/`, starts Crown services, and launches required agent profiles. Set `WORLD_NAME` to select a specific world manifest; otherwise, the default manifest is used.
