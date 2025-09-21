# Stage C Scripted Demo Rehearsal Summary

The Stage C rehearsal script was executed twice using the synthetic harness to
mirror production telemetry capture. Evidence for both sessions is archived
under `logs/stage_c_demo/20250921T172855Z/` with raw audio waveforms, avatar
frame bundles, telemetry manifests, and emotion-stream logs for each beat.

## Session overview

| Session | Seed | Evidence directory | Steps | Dropouts detected | Max sync offset (s) |
|---------|------|-------------------|-------|-------------------|---------------------|
| 1 | 101 | `logs/stage_c_demo/20250921T172855Z/session_01/` | 3 | No | 0.067 |
| 2 | 202 | `logs/stage_c_demo/20250921T172855Z/session_02/` | 3 | No | 0.067 |

Both runs completed without audio dropouts or avatar/video sync failures. The
maximum audio/video timing delta observed across beats stayed within 67 ms.

## Telemetry bundle contents

Each session directory contains:

- `audio/` – Base64-encoded float32 waveforms for every scripted beat.
- `video/` – Base64-encoded avatar frame sequences aligned with the audio cues.
- `emotion/stream.jsonl` – Emotion stream emitted per beat.
- `telemetry/events.jsonl` – Step-by-step timing telemetry with sync offsets.
- `telemetry/summary.json` and `telemetry/run_summary.json` – Session metrics.
- `telemetry/media_manifest.json` – Relative asset paths for auditors.
- `run.log` – Console feed recorded during the run for real-time monitoring.

Reviewers can load the JSONL telemetry to confirm no `dropout=true` events were
emitted and inspect the synced audio/video durations recorded for each beat.
