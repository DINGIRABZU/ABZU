# Rehearsal Asset Packaging Protocol

The stage B rehearsal directories accumulate large numbers of per-frame JSON
artifacts for audio, video, and emotional telemetry. Tracking those files
in Git produced noisy diffs and frequently pushed pull requests beyond review
limits. This protocol replaces raw asset check-ins with deterministic bundles
and manifests so we can prove provenance without bloating history.

## Packaging Format

Each rehearsal session directory (`logs/stage_b/<run_id>/rehearsals/<session>/`)
now stores a `session_manifest.json` describing the uploaded evidence bundle.
The bundle itself is a gzipped tarball named `<session>_media.tar.gz` created in
`<session>/bundles/`. The tarball contains:

- `audio/` — all generated audio frame JSON records.
- `video/` — media frame JSON descriptors.
- `emotion/` — high-frequency emotional state stream dumps.
- `telemetry/events.jsonl` and `telemetry/media_manifest.json` — verbose event
  ledgers that are useful for forensic review but unnecessary for day-to-day
  diffs.

The manifest captures:

- Stage, run, and session identifiers.
- UTC generation timestamp.
- Bundle metadata: filename, size, SHA-256 checksum, source members, and the
  evidence-store URI where the tarball is published.
- `retained_files` — lightweight logs (e.g., `run.log`, summary JSON) kept in Git
  for quick inspection.

A run-level `rehearsal_manifest.json` lives in `logs/stage_b/<run_id>/rehearsals/`
so doctrine and automation can discover all bundles associated with the run.

## Tooling

Use `scripts/package_rehearsal_assets.py` to create bundles and manifests. The
script accepts one or more session paths and can optionally prune packaged
artifacts from the working tree once the tarball is written.

```bash
python scripts/package_rehearsal_assets.py \
  logs/stage_b/20250921T230434Z/rehearsals/session_01 \
  --artifact-base-uri evidence://stage-b \
  --prune
```

- `--artifact-base-uri` defaults to the `EVIDENCE_BASE_URI` environment variable
  or `evidence://stage-b` when unset. Point this to the canonical evidence
  bucket/location.
- When `--prune` is supplied the script removes `audio/`, `video/`, `emotion/`,
  and the verbose telemetry files after the tarball is generated so they are not
  accidentally committed.
- The tarball is written to `<session>/bundles/`. That path is ignored by Git;
  upload the bundle to the evidence store and then remove it locally if desired.

Pre-commit now runs `python scripts/check_rehearsal_bundles.py` whenever files
under `logs/stage_b/` change. The hook fails if raw high-churn artifacts remain,
if manifests are missing, or if bundles are staged for commit.

## Contributor Workflow

1. Run the packaging script for each new rehearsal session.
2. Upload the generated tarball(s) to the shared evidence store at the URI noted
   in `session_manifest.json`.
3. Commit the manifest(s) and any lightweight retained files.
4. Verify `rehearsal_manifest.json` captures all sessions in the run.
5. Execute `pre-commit run --all-files` (or allow it to run automatically) to
   confirm no high-churn files remain.

Following this flow keeps Git-friendly diffs while maintaining a verifiable map
from manifests to the full telemetry stored in the evidence archive.
