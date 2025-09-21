# Stage C Rehearsal Runs (Run1 & Run2)

## Overview
- **Run 1 directory:** `logs/stage_c_demo/run1`
  - Telemetry bundle: `logs/stage_c_demo/run1/telemetry_bundle.zip.b64`
  - Sessions: `session01`, `session02`
- **Run 2 directory:** `logs/stage_c_demo/run2`
  - Telemetry bundle: `logs/stage_c_demo/run2/telemetry_bundle.zip.b64`
  - Sessions: `session01`, `session02`

All sessions completed TTS synthesis and avatar rendering; however, each triggered an audio playback dropout because `ffmpeg` is not installed on the host, matching prior expectations for the production-like container.

## Session Health Snapshot

| Run | Session | Emotion / Layer | Window (UTC) | Telemetry Events | Dropouts | Notes |
| --- | ------- | ---------------- | ------------ | ---------------- | -------- | ----- |
| Run 1 | session01 | devotion / albedo_layer | 2025-09-21T16:49:16Z → 2025-09-21T16:49:20Z | 1 | 1 | audio.play_sound failed (`ffmpeg_missing`) |
| Run 1 | session02 | reverence / rubedo_layer | 2025-09-21T16:49:20Z → 2025-09-21T16:49:20Z | 1 | 1 | audio.play_sound failed (`ffmpeg_missing`) |
| Run 2 | session01 | devotion / albedo_layer | 2025-09-21T16:49:39Z → 2025-09-21T16:49:43Z | 1 | 1 | audio.play_sound failed (`ffmpeg_missing`) |
| Run 2 | session02 | reverence / rubedo_layer | 2025-09-21T16:49:43Z → 2025-09-21T16:49:44Z | 1 | 1 | audio.play_sound failed (`ffmpeg_missing`) |

Refer to each run's `summary.md` for embedded artifact pointers and decode instructions. Emotion stream deltas are stored as `emotion_stream.jsonl` alongside telemetry JSON snapshots.
