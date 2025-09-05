# Operator Protocol

Operator actions dispatched via the API include a unique `command_id` UUID.
The identifier is returned in responses, streamed over `/operator/events`, and
propagated to Crown and RAZAR logs.

Each command generates an entry in `logs/operator_commands.jsonl`:

```
{"command_id": "<uuid>", "agent": "<target>", "result": {...}, "started_at": "<iso>", "completed_at": "<iso>"}
```

Use the `command_id` to trace outcomes across systems and audit activity.
