# World Bootstrap

Utilities for cloning and updating world configuration.

## Cloning a World

Export the current world's settings and import them elsewhere.

```bash
python -m worlds export world.json
# transfer world.json to another environment
python -m worlds import world.json --world new_world
```

## Updating a World

Snapshot the configuration before applying patches or changes.

```bash
python -m worlds export backup.json
# apply updates to the running system
python -m worlds import backup.json
```
