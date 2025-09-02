# Crown Overview

This overview is deprecated; see [Crown Guide](Crown_GUIDE.md) for full details.

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

For connector registration requirements, consult the [Connector Registry Protocol](The_Absolute_Protocol.md#connector-registry-protocol) and the [Connector Index](connectors/CONNECTOR_INDEX.md).

