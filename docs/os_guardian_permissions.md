# OS Guardian Permission Policies

The `safety` module guards high-risk actions executed by the OS Guardian
utilities. Permissions are configured with environment variables so deployments
can choose an appropriate security posture.

## Variables

- `OG_ALLOWED_APPS` – colon-separated list of executable names or paths that may
  be launched with `open_app`.
- `OG_ALLOWED_DOMAINS` – colon-separated list of domains that `open_url` is
  permitted to access.
- `OG_ALLOWED_COMMANDS` – colon-separated list of command names allowed via
  `run_command`. Defaults to `echo`, `ls`, `pwd` and `cat` if unset.
- `OG_POLICY` – behaviour when an action is requested that may have side
  effects. Set to `allow` (default) to run automatically, `ask` to prompt for
  confirmation or `deny` to block.

Rollback handlers registered by `safety.register_undo()` can be triggered with
`undo_last()` or `undo_all()` if reversible actions were performed.
