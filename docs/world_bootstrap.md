# World Bootstrap

Guide to initializing a world and preserving its component configuration.

## Registry
- The [`worlds.config_registry` module](../worlds/config_registry.py) tracks per-world metadata.
- Layers are registered when memory modules load; agent packages register during import.
- Brokers, model paths, and other resources can be registered with dedicated helpers.

## Export and Import
- Use `python -m worlds export <path>` or [`python scripts/world_export.py`](../scripts/world_export.py) to save configuration.
- `python -m worlds import <path>` restores a previously exported JSON file.
- The `WORLD_NAME` environment variable selects which world to target; defaults to `"default"`.

## Workflow
1. Import `memory` and `agents` to populate layers and agent names.
2. Register brokers or model locations as needed using `register_broker` and `register_model_path`.
3. Export the configuration to capture the world's state.
4. Import the file on another system to reproduce the same setup.
