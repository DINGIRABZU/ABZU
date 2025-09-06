# World Bootstrap Workflow

This guide outlines how to initialise a world and verify its configuration.

1. Run `python scripts/bootstrap_world.py` to set up memory layers, start Crown services and load required agents.
2. Validate the configuration registry with `python scripts/validate_world_registry.py`. The script imports registered layers and agents and reports any entries that do not correspond to components in the repository.
3. The validator is integrated with pre-commit, so it executes automatically when world components change. It can also be run manually when adjusting world settings.

Keeping the registry accurate ensures world bootstrapping uses valid components and prevents missing dependencies at runtime.
