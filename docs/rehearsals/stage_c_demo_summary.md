# Stage C Scripted Demo Rehearsal Summary

The Stage C2 scripted demo storyline replays Stage B session `session_01` from
run `20250921T230434Z`, but the harness now keeps the repository binary-free by
default. Audio and video directories under
`logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline/` contain
only guard `.gitignore` files, while telemetry references the Stage B evidence
bundle recorded in the session manifest.【F:logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline/audio/.gitignore†L1-L3】【F:logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline/video/.gitignore†L1-L3】【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/session_manifest.json†L1-L19】

The follow-up capture `20250928T162716Z-stage_c2_demo_storyline` keeps only
sentinel `.gitignore` files in its audio/video directories while the
corresponding manifest points reviewers back to the Stage B bundle so binaries
never land in git.【F:logs/stage_c/20250928T162716Z-stage_c2_demo_storyline/demo_storyline/audio/.gitignore†L1-L3】【F:logs/stage_c/20250928T162716Z-stage_c2_demo_storyline/demo_storyline/video/.gitignore†L1-L3】【F:evidence_manifests/stage-c-demo-storyline.json†L1-L19】
Downloaders should rely on the recorded evidence URI from the Stage B manifest
and hydrate the stems on demand with
`scripts/stage_c_scripted_demo.py --copy-media` when local playback is
necessary.【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/session_manifest.json†L7-L19】【F:evidence_manifests/stage-b-audio.json†L2-L40】【F:scripts/stage_c_scripted_demo.py†L369-L441】

The Stage B rehearsal summary confirms the storyline covers three scripted
beats, finishes without dropouts, and tops out at a 67 ms sync offset, which the
Stage C replay reproduces when sourcing media from the bundle.【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L1-L23】

## Session overview

| Source Stage B run | Stage C evidence root | Steps | Dropouts detected | Max sync offset (s) |
| --- | --- | --- | --- | --- |
| `20250921T230434Z` / `session_01` | `logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline/` | 3 | No | 0.067 |

## Telemetry and provenance workflow

`scripts/stage_c_scripted_demo.py` now emits provenance entries that point back
to the Stage B bundle (URI + SHA-256) unless `--copy-media` is explicitly
provided, keeping Stage C outputs light while preserving integrity metadata for
auditors.【F:scripts/stage_c_scripted_demo.py†L369-L441】【F:scripts/stage_c_scripted_demo.py†L512-L590】

To fetch stems locally when deep inspection is required:

1. Pull the Stage B evidence bundle recorded in the session manifest at
   `evidence://stage-b/stage_b/20250921T230434Z/session_01/session_01_media.tar.gz`
   (SHA-256 `0a862de4…`).【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/session_manifest.json†L7-L19】
2. Run the harness with `--copy-media` to materialize audio/video alongside the
   Stage C telemetry, e.g.:

   ```bash
   python scripts/stage_c_scripted_demo.py logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline \
       --stage-b-run logs/stage_b/20250921T230434Z \
       --stage-b-session session_01 \
       --copy-media
   ```

   The flag mirrors the Stage B bundle into the output if you need offline
   playback; omit it to keep the repository binary-free.【F:scripts/stage_c_scripted_demo.py†L441-L472】【F:scripts/stage_c_scripted_demo.py†L608-L696】

The generated `telemetry/run_summary.json` and `telemetry/media_manifest.json`
capture the provenance data and step metrics, ensuring reviewers can validate
the storyline without committing large media artifacts.【F:scripts/stage_c_scripted_demo.py†L512-L590】
