# Feature Specifications

Guidelines for authoring feature specification files.

## Authoring
1. Copy [FEATURE_TEMPLATE.md](FEATURE_TEMPLATE.md) to `docs/features/<feature_name>.md`.
2. Fill out each section with concise, actionable details.
3. Update [`docs/index.md`](../index.md) and regenerate [`docs/INDEX.md`](../INDEX.md) with `python tools/doc_indexer.py`.
4. Run `pre-commit run --files <new_file> docs/index.md docs/INDEX.md` before committing.

## Storage
Store completed specifications in this directory. Use kebab-case or snake_case filenames that reflect the feature being described.

