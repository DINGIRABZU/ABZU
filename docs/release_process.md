# Release Process

This guide covers signing build artifacts and verifying their integrity.

## Signing Build Artifacts

1. Generate release artifacts in a directory, for example `dist/`.
2. Run the signing script with the project GPG key:
   ```bash
   python scripts/sign_release.py dist --key-id <GPG_KEY_ID>
   ```
3. The script writes SHA256 checksums and signatures to `release/manifest.json`.

## Verifying Signatures

1. Ensure the public portion of the project key is imported into your keyring.
2. Validate artifacts against the manifest:
   ```bash
   python scripts/verify_release_signature.py dist
   ```
3. The verifier checks each checksum and GPG signature.

## Version History

- 2025-09-20: Documented release signing and verification workflow.
