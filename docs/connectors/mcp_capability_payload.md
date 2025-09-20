# MCP Capability Payload

The Neo-APSU connector template exchanges capabilities with the MCP gateway
during the `/handshake` ritual. The payload confirms the connector identity,
declares supported contexts, and provides token rotation metadata so the
gateway can validate rehearsal credentials.

## JSON Schema

```json
{
  "type": "object",
  "required": ["identity", "supported_contexts", "rotation"],
  "properties": {
    "identity": {
      "type": "object",
      "required": ["connector_id", "version", "instance"],
      "properties": {
        "connector_id": {"type": "string", "description": "Stable registry id."},
        "version": {"type": "string", "description": "Semantic version exposed by the connector."},
        "instance": {"type": "string", "description": "Deployment or rehearsal identifier."}
      }
    },
    "supported_contexts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "channels", "capabilities"],
        "properties": {
          "name": {"type": "string", "description": "Context identifier advertised to the gateway."},
          "channels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Signal surfaces enabled for this context (e.g., handshake, heartbeat)."
          },
          "capabilities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Operations supported for the context (register, telemetry, etc.)."
          }
        }
      },
      "minItems": 1
    },
    "rotation": {
      "type": "object",
      "required": ["last_rotated", "rotation_window", "supports_hot_swap", "token_hint"],
      "properties": {
        "last_rotated": {"type": "string", "format": "date-time", "description": "Timestamp of the current credential rotation."},
        "rotation_window": {"type": "string", "description": "ISO-8601 duration specifying when the next rotation is due."},
        "supports_hot_swap": {"type": "boolean", "description": "Whether the connector can rotate tokens without downtime."},
        "token_hint": {"type": "string", "description": "Non-secret identifier describing the active credential batch."},
        "credentials": {
          "type": "object",
          "required": ["type", "token"],
          "properties": {
            "type": {"type": "string", "enum": ["bearer"], "description": "Authentication method presented to the gateway."},
            "token": {"type": "string", "description": "Shared secret or signed bearer token for the handshake."}
          }
        }
      }
    }
  }
}
```

### Sample Payload

```json
{
  "identity": {
    "connector_id": "neo_apsu_connector_template",
    "version": "0.2.0",
    "instance": "local"
  },
  "supported_contexts": [
    {
      "name": "stage-b-rehearsal",
      "channels": ["handshake", "heartbeat"],
      "capabilities": ["register", "telemetry"]
    }
  ],
  "rotation": {
    "last_rotated": "2025-10-01T00:00:00Z",
    "rotation_window": "PT24H",
    "supports_hot_swap": true,
    "token_hint": "local",
    "credentials": {
      "type": "bearer",
      "token": "<redacted>"
    }
  }
}
```

### Environment Overrides

| Variable | Purpose | Default |
| --- | --- | --- |
| `MCP_CONNECTOR_ID` | Override the `identity.connector_id` field. | `neo_apsu_connector_template` |
| `MCP_CONNECTOR_INSTANCE` | Distinguish rehearsal or deployment targets. | `local` |
| `MCP_LAST_ROTATED` | Provide a known credential rotation timestamp. | current UTC time |
| `MCP_ROTATION_WINDOW` | ISO-8601 duration before the next rotation. | `PT24H` |
| `MCP_SUPPORTS_HOT_SWAP` | Toggle `rotation.supports_hot_swap`. | `true` |
| `MCP_ROTATION_HINT` | Human-readable credential batch label. | `local` |
| `MCP_CONNECTOR_TOKEN` | Bearer token injected into `rotation.credentials`. | not included |
| `MCP_SUPPORTED_CONTEXTS` | JSON array to override `supported_contexts`. | Stage B defaults |

## Handshake Response Validation

The connector expects the gateway to return:

- `authenticated: true` – confirms the credential is valid.
- `session.id` – opaque identifier recorded for telemetry correlation.
- `accepted_contexts` – list of accepted context names or objects. The
  Stage B rehearsal context (`stage-b-rehearsal`) must be acknowledged to
  continue the session.

Unacknowledged contexts or non-authenticated responses trigger exponential
backoff retries before the connector raises an error.

## Stage B Rehearsal Logging

Successful handshakes emit an info log with the event `mcp.handshake`, the
Stage indicator (`B`), the returned `session_id`, and the sanitized list of
accepted contexts. Operators should see entries similar to:

```
INFO connectors.neo_apsu_connector_template Stage B rehearsal handshake acknowledged {'event': 'mcp.handshake', 'stage': 'B', 'session_id': 'sess-123', 'accepted_contexts': ['stage-b-rehearsal']}
```

These logs satisfy the Stage B rehearsal requirement to document the capability
exchange prior to emitting heartbeat telemetry.
