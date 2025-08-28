# Feature Specifications

Guidelines for authoring feature specification files.

## Authoring
1. Copy [FEATURE_TEMPLATE.md](FEATURE_TEMPLATE.md) to `docs/features/<feature_name>.md`.
2. Fill out each section with concise, actionable details.
3. Add the new file to [Blueprint Export](../BLUEPRINT_EXPORT.md) under **Feature Specs**.
4. Update [`docs/index.md`](../index.md) and regenerate [`docs/INDEX.md`](../INDEX.md) with `python tools/doc_indexer.py`.
5. Run `pre-commit run --files <new_file> ../BLUEPRINT_EXPORT.md ../index.md ../INDEX.md` before committing.

## Storage
Store completed specifications in this directory using kebab-case or snake_case filenames. Each spec **must** be referenced in `docs/BLUEPRINT_EXPORT.md`.

