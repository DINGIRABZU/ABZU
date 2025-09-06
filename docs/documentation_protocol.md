# Documentation Protocol

Standard workflow for updating documentation and guides.

1. **Check for applicable `AGENTS.md` instructions** to understand directory-specific conventions.
2. **Follow the [Arcade Theme Style Guide](style_guides/arcade_theme.md)** for color and typography rules.
3. **Update all related documents** whenever a component or guide changes to keep information synchronized.
4. **Sync `docs/system_blueprint.md`** whenever components or documentation change to keep the architectural overview current.
5. **Ensure `docs/INDEX.md` stays current.** The `doc-indexer` pre-commit hook regenerates the index
   automatically when files in `docs/` change, skipping `node_modules`, `dist`, and `build`
   directories to avoid indexing generated artifacts.
6. **Validate changes with** `pre-commit run --files <changed_files>` **before committing.**
7. **Use traceable commit messages** that capture the rationale for changes and reference affected documents.

