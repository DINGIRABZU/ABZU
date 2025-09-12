#!/bin/sh
# Build wheels for the core, memory, and vector crates
set -e
for crate in core memory vector; do
    maturin build --release -m "$crate/Cargo.toml" "$@"
done
