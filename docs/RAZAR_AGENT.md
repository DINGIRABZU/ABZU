# RAZAR Remote Agent Loader

The RAZAR environment can pull helper agents from HTTP endpoints or Git
repositories at runtime.  These agents extend the system without requiring a
local installation.

Remote modules must define two functions:

``configure()``
: returns a mapping of runtime options.

``patch(context)``
: returns a patch suggestion or replacement source code.  Interactions are
logged to `logs/razar_remote_agents.json` for later audit.

## Loading an agent

```python
from agents.razar import remote_loader

module, config, suggestion = remote_loader.load_remote_agent(
    "example_agent", "https://example.com/agent.py"
)
```

## Automatic patching

When tests fail, `patch_on_test_failure` can request a patch from the remote
agent, apply it inside a temporary sandbox and rerun the affected tests.  The
change is copied back into the repository only if the tests succeed.

```python
from pathlib import Path

remote_loader.patch_on_test_failure(
    "example_agent",
    "https://example.com/agent.py",
    Path("pkg/module.py"),
    [Path("tests/test_module.py")],
)
```

