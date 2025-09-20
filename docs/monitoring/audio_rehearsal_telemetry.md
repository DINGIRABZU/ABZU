# Audio Rehearsal Telemetry

Stage B sign-off requires operators to archive audio playback and modulation
metrics for each rehearsal. The new instrumentation added to
`modulation_arrangement` and `src/audio/engine` emits structured telemetry that
can be collected in two complementary ways:

1. **Structured logs.** All events are written through the
   `abzu.telemetry.audio` logger in JSON form. Point your log shipper at the
   Python process and filter on `telemetry=` entries to forward them to your
   aggregation system.
2. **In-memory collector.** Import `telemetry` from `src.audio.telemetry` to
   snapshot or clear metrics inside orchestration scripts:

   ```python
   from src.audio.telemetry import telemetry

   telemetry.clear()
   ...  # run rehearsal
   snapshot = telemetry.get_events()
   ```

## Event catalog

The tables below summarise the primary signals surfaced by the collector. All
events include `timestamp` (Unix seconds) and the emitting `event` name.

| Event | Description | Key fields |
| ----- | ----------- | ---------- |
| `modulation.layer_stems` | Execution timing for stem overlays. | `status`, `backend`, `stem_count`, `duration_s` |
| `modulation.export_mix` | Audio render/export lifecycle. | `status`, `path`, `format`, `duration_s`, `error` |
| `modulation.export_session` | DAW session export outcomes and fallbacks. | `status`, `session_format`, `audio_path`, `session_path`, `available`, `remediation` |
| `audio.play_sound` | Playback attempts, including failure reasons and loop modes. | `status`, `mode`, `reason`, `duration_s`, `path` |
| `audio.play_segment` | Backend utilisation and playback latency. | `status`, `backend`, `duration_s`, `error` |
| `audio.loop_play_iteration` | Progress for long-running rehearsal loops. | `status`, `iteration`, `requested_loops` |
| `audio.stop_all` | Confirmation that rehearsals were stopped cleanly. | `status` |

### Sample output

The snippet below shows representative events captured during a rehearsal dry
run. Values are truncated for readability.

```json
{
  "event": "modulation.layer_stems",
  "status": "success",
  "stem_count": 3,
  "backend": "pydub",
  "duration_s": 0.042
}
{
  "event": "audio.play_sound",
  "status": "completed",
  "mode": "single",
  "path": ".../cue.wav",
  "duration_s": 1.51
}
{
  "event": "modulation.export_session",
  "status": "fallback",
  "session_format": "ardour",
  "remediation": "Install Ardour and ensure its binary is on PATH or disable Ardour session export.",
  "available": {"ardour": false}
}
```

## Stage B review checklist

During Stage B rehearsals, operators should:

1. Clear the collector (`telemetry.clear()`) before each run.
2. After the run completes, snapshot events with
   `telemetry.get_events()` and archive them alongside rehearsal notes.
3. Confirm that every `audio.play_sound` event either ends in
   `status="completed"` or is matched by a `stop_all` entry.
4. Investigate any `status="failure"` or `status="fallback"` events and
   capture remediation actions in the rehearsal log.
5. Export the JSON stream to the observability platform used in Stage A to
   maintain continuity of dashboards and alerts.

Following this workflow provides auditable evidence that modulation layering,
session export, and playback systems operated without dropouts and that
fall-back procedures were followed when toolchains were unavailable.
