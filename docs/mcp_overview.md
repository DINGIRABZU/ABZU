# MCP Gateway Overview

The MCP gateway bridges existing FastAPI services with the Model Context Protocol.
It exposes context registration and model invocation over MCP while continuing to
serve the legacy HTTP routes.

## Configuration
- `config/mcp.toml` defines model paths, rate limits, and API keys.

## Endpoints
- **`/context/register`** – register conversation context.
- **`/model/invoke`** – invoke a configured model.

## Building Neo‑APSU Connectors

1. Start with the scaffold in `connectors/neo_apsu_connector_template.py`.
2. Implement the MCP handshake and capability exchange.
3. Emit heartbeat telemetry and validate with `ConnectorHeartbeat`.
4. Confirm doctrine compliance and run `python scripts/check_connectors.py`.
5. Verify readiness using the [Connector Health Protocol](connector_health_protocol.md).
6. Append the connector's spec to [mcp_connectors.md](mcp_connectors.md).

## Version History
- 2025-10-??: Initial version.

Backlinks: [Blueprint Spine](blueprint_spine.md)
