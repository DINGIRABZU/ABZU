# MCP Migration Guide

This guide explains how to convert existing API connectors to the **Model Context Protocol (MCP)**.

## Rationale

MCP supplies a shared handshake, authentication, and logging layer for internal
services. Migrating connectors reduces bespoke HTTP clients and makes call
traces easier for operators to follow.

## Conversion Steps

1. **Wrap the connector with an MCP server.** Expose actions as MCP commands and
   list available capabilities.
2. **Implement a client shim.** Replace direct HTTP requests with an
   `mcp.Client` that negotiates versions and sends structured payloads.
3. **Update the registry.** Mark the entry in
   [CONNECTOR_INDEX.md](CONNECTOR_INDEX.md) with `status: migrating` or `mcp`
   once complete. Reference any interim adapters (for example
   `OperatorMCPAdapter`) so Stage B rehearsals can track coverage.
4. **Revise schemas and tests.** Provide a JSON or YAML schema for the MCP
   surface and expand unit tests to cover the handshake and error paths. Stage B
   rehearsal smoke tests (`scripts/stage_b_smoke.py`) should exercise all
   connectors listed in the `STAGE_B_TARGET_SERVICES` constant.

### Example: Converting `operator_api`

```python
# before: direct HTTP call
resp = requests.post("/operator/command", json=payload)

# after: MCP client
from mcp import Client

with Client("operator_api") as client:
    resp = client.start_call("command", payload)
```

### Common Pitfalls

- Missing capability declarations cause runtime negotiation failures.
- Old HTTP endpoints left in the code path produce duplicate requests.
- Connector index entries not updated to `mcp` status.
- Schemas omitted or out of sync with implemented commands.

Following these steps keeps connectors consistent and discoverable as MCP
replaces ad‑hoc HTTP implementations across the stack.
