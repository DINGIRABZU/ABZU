# RAZAR Logging Guidelines

The mission logger records component activity in `logs/razar.log` using one JSON
object per line. Each entry contains:

- `event` – type of action (`start`, `health`, `quarantine`, `patch`)
- `component` – name of the component
- `status` – outcome or note for the event
- `timestamp` – UTC time the event occurred
- `details` – optional free-form context

## Recording events

Use `agents.razar.mission_logger` or the command line interface to append
entries:

```bash
python -m razar.mission_logger log gateway success --event start
python -m razar.mission_logger log gateway fail --event health --details "timeout"
python -m razar.mission_logger log gateway patched --event patch --details "1.2.3"
```

## Inspecting the timeline

For debugging, reconstruct the full sequence of events:

```bash
python -m razar timeline
```

The output lists each entry in chronological order, making it easy to identify
when failures or quarantines occurred.
