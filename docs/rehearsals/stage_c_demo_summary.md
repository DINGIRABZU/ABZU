# Stage C Scripted Demo Rehearsal Summary

The Stage C scripted demo storyline was executed through the operator Stage C2
workflow, which invokes `scripts/stage_c_scripted_demo.py` with a deterministic
`--seed 42`. The latest evidence is archived at
`logs/stage_c/20250923T221242Z-stage_c2_demo_storyline/`, where the harness
stores audio/video stems, telemetry, and the emotion stream beneath the
`demo_storyline/` directory.

## Session overview

| Run | Seed | Evidence directory | Steps | Dropouts detected | Max sync offset (s) |
|-----|------|-------------------|-------|-------------------|---------------------|
| 1 | 42 | `logs/stage_c/20250923T221242Z-stage_c2_demo_storyline/demo_storyline/` | 3 | No | 0.067 |

The run completed without audio dropouts or avatar/video sync failures. The
maximum audio/video timing delta observed across beats stayed within 67 ms,
matching the rehearsal target for the storyline cues.

## Telemetry bundle contents

The storyline directory provides:

- `audio/` – Base64-encoded float32 waveforms for every scripted beat.
- `video/` – Base64-encoded avatar frame sequences aligned with the audio cues.
- `emotion/stream.jsonl` – Emotion stream emitted per beat.
- `telemetry/events.jsonl` – Step-by-step timing telemetry with sync offsets.
- `telemetry/summary.json` and `telemetry/run_summary.json` – Session metrics
  exported by the demo harness.
- `telemetry/media_manifest.json` – Relative asset paths for auditors to load
  associated stems.

Reviewers can load the JSONL telemetry to confirm no `dropout=true` events were
emitted and inspect the synced audio/video durations recorded for each beat.
