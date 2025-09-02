# Operator Protocol

This guide is deprecated; see [Operator Interface Guide](operator_interface_GUIDE.md) for full instructions.

## Mission Brief Example

```json
{
  "priority_map": {"signal": 1},
  "current_status": {"signal": "ready"},
  "open_issues": []
}
```

## Operator Chat Example

```bash
curl -X POST localhost:8000/operator/command \\
  -H 'Authorization: Bearer <token>' \\
  -d '{"operator":"crown","agent":"razar","command":"status"}'
```

See the [Connector Registry Protocol](The_Absolute_Protocol.md#connector-registry-protocol) and the [Connector Index](connectors/CONNECTOR_INDEX.md) for registration requirements.

