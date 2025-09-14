# CI Guide

This guide outlines how ABZU's continuous integration checks run and how to replicate them locally.

## Rust checks

The CI pipeline validates Rust code with:

- `cargo fmt --all -- --check`
- `cargo clippy --all-targets --all-features -- -D warnings`
- `cargo test --workspace --all-features`

## Pre-commit hooks

Run `pre-commit run --files <modified files>` before committing. This repository also requires:

- `pre-commit run verify-onboarding-refs`

## Registration checks

- New Rust crates must appear in `docs/system_blueprint.md` and related doctrine.
- New documentation files must be listed in `docs/INDEX.md`.

For a summary of workflow jobs, see [CI Overview](CI_OVERVIEW.md).
