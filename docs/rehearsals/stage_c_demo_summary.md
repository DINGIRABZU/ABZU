# Stage C Scripted Demo Rehearsal Summary

The Stage C2 storyline replay uses Stage B run `20250921T230434Z` (`session_01`)
as its canonical source. Earlier captures keep the repository binary-free by
storing only sentinel `.gitignore` files beneath `audio/` and `video/`, and the
session manifest lists the evidence URI for on-demand extraction.【F:logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline/audio/.gitignore†L1-L4】【F:logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline/video/.gitignore†L1-L4】【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/session_manifest.json†L1-L23】

The `/alpha/stage-c2-demo-storyline` run `20251001T085114Z-stage_c2_demo_storyline`
regenerated the replay after the Stage B bundle refresh. The new summary and
telemetry show the storyline completing three cues with zero dropouts, carry
forward the 67 ms sync ceiling, and embed SHA-256 fingerprints for the Stage B
media that was referenced during playback.【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/summary.json†L1-L78】【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/demo_storyline/telemetry/summary.json†L1-L65】【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/telemetry/run_summary.json†L1-L7】

The evidence manifests now follow the repository packaging policy. `stage-b-audio.json`
lists every cue metadata file, telemetry export, and checksum for the Stage B
archive, while `stage-c-demo-storyline.json` records the fresh Stage C archive
name, digest, and upload hint so reviewers can retrieve the replay bundle
without committing media to git.【F:evidence_manifests/stage-b-audio.json†L1-L77】【F:evidence_manifests/stage-c-demo-storyline.json†L1-L40】

Downloaders should rely on those manifests plus the session manifest to hydrate
stems on demand via `scripts/stage_c_scripted_demo.py --copy-media`. Setting
`EVIDENCE_GATEWAY_BASE_URL` allows the harness to fetch the Stage B archive when
local assets are absent, while the default mode keeps only telemetry summaries
inside `logs/stage_c/` for auditing.【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/session_manifest.json†L7-L19】【F:scripts/stage_c_scripted_demo.py†L152-L208】【F:scripts/stage_c_scripted_demo.py†L441-L472】

## Session overview

| Source Stage B run | Stage C evidence root | Steps | Dropouts detected | Max sync offset (s) |
| --- | --- | --- | --- | --- |
| `20250921T230434Z` / `session_01` | `logs/stage_c/20250928T130000Z-stage_c2_demo_storyline/demo_storyline/` | 3 | No | 0.067 |
| `20250921T230434Z` / `session_01` | `logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/demo_storyline/` | 3 | No | 0.067 |

## Telemetry and provenance workflow

`scripts/stage_c_scripted_demo.py` emits provenance entries that point back to
the Stage B bundle (URI + SHA-256) unless `--copy-media` is explicitly provided,
preserving integrity metadata while keeping the repository binary-free.【F:scripts/stage_c_scripted_demo.py†L369-L441】【F:scripts/stage_c_scripted_demo.py†L512-L590】

To fetch stems locally when deep inspection is required:

1. Point `EVIDENCE_GATEWAY_BASE_URL` at the evidence proxy and pull the Stage B
   bundle referenced in `session_manifest.json` (SHA-256 `7d7e5f8f…`). Use the
   upload hints recorded in the evidence manifests if a direct proxy fetch is
   necessary.【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/session_manifest.json†L7-L23】【F:evidence_manifests/stage-b-audio.json†L9-L19】【F:evidence_manifests/stage-c-demo-storyline.json†L1-L12】
2. Run the harness with `--copy-media` to materialize audio/video alongside the
   Stage C telemetry:

   ```bash
   python scripts/stage_c_scripted_demo.py logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/demo_storyline \
       --stage-b-run logs/stage_b/20250921T230434Z \
       --stage-b-session session_01 \
       --copy-media
   ```

   The flag mirrors the Stage B bundle into the output if offline playback is
   required; omit it to keep the repository lightweight.【F:scripts/stage_c_scripted_demo.py†L441-L472】【F:scripts/stage_c_scripted_demo.py†L608-L696】

The generated `telemetry/run_summary.json` and `telemetry/media_manifest.json`
capture the provenance data and step metrics, ensuring reviewers can validate
the storyline without committing large media artifacts.【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/demo_storyline/telemetry/run_summary.json†L1-L63】【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/demo_storyline/telemetry/media_manifest.json†L1-L138】
