# Setup Quickstart

Spin up a minimal world configuration using file-backed memory layers.

## Minimal World

1. Install the core dependencies:
   ```bash
   pip install -e .[minimal]
   ```
2. Populate mandatory layers with default records:
   ```bash
   python scripts/bootstrap_world.py
   ```
   The script reports progress as each layer is initialized.

## Next Steps

- Inspect generated data under `data/` to review the seeded layers.
- Run `scripts/list_layers.py` to verify active memory layers.
