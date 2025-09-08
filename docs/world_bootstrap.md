# World Bootstrap

Guidelines for seeding and cloning world configurations.

## Initialize a world

Use `initialize_world` to record available layers and agents for a new world.

```python
from worlds import initialize_world, export_config_file

initialize_world(
    layers=["cortex", "limbic"],
    agents=["zeus", "hera"],
    world="olympus",
)
export_config_file("olympus.json", world="olympus")
```

## Clone an existing world

Configuration snapshots can be imported into a different world to clone its
setup.

```python
from worlds import import_config_file

import_config_file("olympus.json", world="asgard")
```

`asgard` now inherits the layers and agents defined for `olympus`.
