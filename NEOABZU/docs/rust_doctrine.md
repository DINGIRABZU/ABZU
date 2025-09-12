# Rust Doctrine

This primer captures expectations for Rust code within NEOABZU.

## Naming

- Use `snake_case` for files, modules, functions, and variables.
- Exported types and traits use `CamelCase`.
- Crate names should match their directory and use `snake_case`.
- Align with general repository conventions in [coding_style.md](../../docs/coding_style.md).

## Module Layout

- Each crate defines a `Cargo.toml` and a `src/` tree.
- Public APIs live in `lib.rs`; binaries use `main.rs`.
- Submodules mirror their filesystem path and avoid circular dependencies.
- Shared utilities belong in `core` crates reused across workspaces.

## Tests

- Place unit tests in the same module using `#[cfg(test)]` blocks or in `tests/` directories for integration tests.
- Run `cargo test` before committing.
- Tests must be deterministic and avoid network calls.

## Pre-commit Checks

Rust files trigger a pre-commit hook that runs:

```bash
cargo fmt --check
cargo clippy
```

These commands ensure formatting and linting remain consistent. Fix issues before committing.
