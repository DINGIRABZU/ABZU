# Evidence Packaging Strategy

This guide defines how rehearsal evidence is collected without committing large
binary payloads to Git while keeping every bundle discoverable for reviewers.
It applies to Stage A guardrails, Stage B rehearsals, and any future milestone
that emits binary artifacts.

## Objectives

- Preserve discoverability through versioned manifests that describe each
  archive, its checksum, and its retrieval URI.
- Keep Git history binary-free by storing heavy evidence in external object
  storage.
- Provide a repeatable workflow so contributors can package rehearsals locally
  and CI can enforce policy before a pull request opens.

## Workflow Overview

1. **Prepare evidence locally.** Generate the rehearsal logs, presets, audio
   renders, and telemetry in a working directory (e.g. `logs/stage_b/latest`).
2. **Package the bundle.** Run
   ```bash
   python scripts/package_evidence.py <bundle-name> <source-dir> \
     --upload-base s3://abzu-stage-b-rehearsals
   ```
   The script creates a gzip archive in `artifacts/evidence/` and writes a
   manifest to `evidence_manifests/<bundle-name>.json`.
3. **Upload the archive.** Push the generated tarball to the shared rehearsal
   bucket (default `s3://abzu-stage-b-rehearsals`). After upload, delete the
   local archive to prevent accidental commits—the manifest preserves the
   checksum and URI.
4. **Commit the manifest.** Include the updated JSON manifest plus any README
   pointers in your pull request. The manifest references the archive filename,
  its SHA-256 digest, and the upload hint used by reviewers.
5. **Document retrieval.** Update affected docs (`system_blueprint.md`, bundle
   guides, READMEs) so reviewers know how to fetch and unpack the evidence.

## Manifest Schema

`evidence_manifests/*.json` records:

- `bundle`: logical bundle identifier used in documentation.
- `created_at`: ISO 8601 timestamp when the manifest was generated.
- `source`: canonical source directory that was packaged.
- `archive`: metadata for the compressed artifact.
  - `filename`: tarball name produced by `package_evidence.py`.
  - `size_bytes`: archive size.
  - `sha256`: archive checksum.
  - `content_type`: MIME type (`application/gzip` or `application/zstd`).
  - `upload_hint`: remote URI where reviewers retrieve the archive.
- `files`: list of packaged files with relative paths, sizes, and SHA-256
  checksums.
- `timestamp`: UTC stamp embedded in the archive filename for auditability.
- `notes`: optional reminders for operators (e.g. upload + delete local copies).

## Tooling & Enforcement

- `scripts/package_evidence.py` packages evidence and emits manifests.
- `scripts/check_evidence_manifests.py` validates JSON structure and checksum
  fields. A dedicated pre-commit hook (`validate-evidence-manifests`) runs on
  changed manifests.
- CI executes the same validation to block pull requests missing upload hints
  or containing malformed manifests.
- The existing `check_no_binaries` hook prevents committing raw audio or other
  binaries alongside manifests.

## Reviewer Retrieval

1. Read the manifest in `evidence_manifests/` and locate the `upload_hint`.
2. Download the archive (example using AWS CLI):
   ```bash
   aws s3 cp s3://abzu-stage-b-rehearsals/stage-b-audio-20250218T120000Z.tar.gz .
   ```
3. Verify the checksum:
   ```bash
   shasum -a 256 stage-b-audio-20250218T120000Z.tar.gz
   ```
   Compare the digest with the manifest value.
4. Extract the archive into a scratch directory for review:
   ```bash
   tar -xzf stage-b-audio-20250218T120000Z.tar.gz -C /tmp/stage-b-audio
   ```

Maintainers should update the Doctrine Index with new bundle hashes once the
archive is uploaded so the canonical ledger references the manifest and stored
artifact.
