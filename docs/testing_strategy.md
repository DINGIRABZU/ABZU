# Testing Strategy

## Contract placeholder suites

CI runs include the placeholder contract suites that live in `tests/contracts/`.
They currently validate JSON fixtures that document crown, identity, memory,
and transport contract evidence. Hardware-only checks are explicitly skipped,
so the suites pass in sandbox CI while still signaling the missing replays.

### Running locally

Run the full placeholder suite—even though the hardware steps skip—to ensure
the shared fixtures remain loadable:

```
pytest tests/contracts
```

When developing locally you can focus on a single module:

```
pytest tests/contracts/test_crown_contract.py
```

Because the hardware paths are decorated with skip markers, these commands will
complete successfully even without the Neo-APSU binaries.

### Extending once binaries ship

When the hardware or sandbox binaries become available:

1. Replace the `TODO hardware replay` skips with assertions that exercise the
   actual handshake, telemetry, and persistence flows.
2. Reuse `tests/contracts/utils.py` for fixture loading so the suite continues
   to skip gracefully if a particular bundle is unavailable.
3. Update the module docstrings with the concrete entry points or CLI commands
   that developers should run to replay the new binaries in CI.
4. Capture any new evidence files in `tests/fixtures/` and document them in the
   corresponding contract page under `docs/contracts/`.

This workflow keeps CI deterministic today while making it obvious how to wire
in the hardware-backed verifications later.
