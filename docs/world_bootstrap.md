# World Bootstrap

Guidelines for seeding and cloning world configurations.

## Initialize a world

Use `initialize_world` to record available layers, agents, and models for a new
world. Additional metadata like model paths and patches can be registered before
exporting the snapshot.

```python
from worlds import (
    export_config_file,
    initialize_world,
    register_model_path,
    register_patch,
)

initialize_world(
    layers=["cortex", "limbic"],
    agents=["zeus", "hera"],
    models=["gpt-4"],
    world="olympus",
)
register_model_path("gpt-4", "/models/gpt-4.bin", world="olympus")
register_patch("gpt-4", "safety-fix", "abc123", world="olympus")
export_config_file("olympus.json", world="olympus")
```

## Clone an existing world

Configuration snapshots can be imported into a different world to clone its
setup.

```python
from worlds import import_config_file

import_config_file("olympus.json", world="asgard")
```

`asgard` now inherits the layers, agents, models, and patch history defined for
`olympus`.
