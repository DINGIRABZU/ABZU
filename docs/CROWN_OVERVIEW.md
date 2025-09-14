# Crown Overview

Crown coordinates mission briefs and routes operator commands across the ABZU stack. It exposes a WebSocket diagnostics channel and REST endpoints for mission handshakes.

## Mission Brief Examples

### Minimal Brief

```json
{
  "priority_map": {"signal": 1},
  "current_status": {"signal": "ready"},
  "open_issues": []
}
```

### Brief with Intel Request

```json
{
  "priority_map": {"signal": 2, "intel": 3},
  "current_status": {"signal": "ready", "intel": "pending"},
  "open_issues": [
    {"id": "missing_feed", "detail": "awaiting reconnaissance data"}
  ]
}
```

## Operator Chat Logs

### HTTP Command

```bash
curl -X POST localhost:8000/operator/command \
  -H 'Authorization: Bearer <token>' \
  -d '{"operator":"crown","agent":"razar","command":"status"}'
```

### WebSocket Session

```
operator> {"command": "status"}
crown> {"status": "ready"}
operator> {"command": "upload", "file": "intel.jpg"}
crown> {"upload": "ack"}
```

For connector registration requirements, consult the [Connector Registry Protocol](The_Absolute_Protocol.md#connector-registry-protocol) and the [Connector Index](connectors/CONNECTOR_INDEX.md).

### Migration Crosswalk

Routing migration details are maintained in the [Migration Crosswalk](migration_crosswalk.md#crown-routing).

