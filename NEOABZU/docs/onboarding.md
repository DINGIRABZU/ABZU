# Onboarding

This Neo‑ABZU guide complements the [ABZU Onboarding Checklist](../../docs/onboarding/README.md); review and confirm both documents in `onboarding_confirm.yml`.

Before diving into Neo‑ABZU specifics, study the core ABZU references: the [Blueprint Spine](../../docs/blueprint_spine.md), [System Blueprint](../../docs/system_blueprint.md), and [The Absolute Protocol](../../docs/The_Absolute_Protocol.md). These texts provide the architectural context and contribution rules assumed throughout this guide.

## Migration Goals

NEOABZU migrates core ABZU capabilities into a lean Rust foundation while preserving operator-first principles and alignment with the original system blueprints.

## Key References

- [ABZU Onboarding Checklist](../../docs/onboarding/README.md)
- [Blueprint Spine](../../docs/blueprint_spine.md)
- [System Blueprint](../../docs/system_blueprint.md)
- [The Absolute Protocol](../../docs/The_Absolute_Protocol.md)
- [Rust Doctrine](rust_doctrine.md) – Rust style, testing, and tooling canon
- [OROBOROS Engine](OROBOROS_Engine.md)
- [OROBOROS Lexicon](OROBOROS_Lexicon.md)
- [Fusion Engine](../fusion/src/lib.rs)
- [Numeric Utilities](../numeric/src/lib.rs)
- [QNL Tier I Glyph Library](QNL_Library.md) – Sumerian lexicon

## Rust Contribution Checklist

When working on Neo-ABZU Rust crates, follow the guardrails summarized in the [Rust Doctrine](rust_doctrine.md):

- Mirror the naming, module layout, and API boundaries specified there so crates align with ABZU's wider style guides.
- Run `cargo fmt --check`, `cargo clippy`, and `cargo test` before sending changes for review; fix all reported issues instead of suppressing them.
- Record doctrine updates in companion documentation such as the [Absolute Protocol](../../docs/The_Absolute_Protocol.md) and ensure `docs/doctrine_index.md` stays accurate.
