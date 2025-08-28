# Documentation Protocol

Standard workflow for updating documentation and guides.

1. **Check for applicable `AGENTS.md` instructions** to understand directory-specific conventions.
2. **Update all related documents** whenever a component or guide changes to keep information synchronized.
3. **Sync `docs/system_blueprint.md`** whenever components or documentation change to keep the architectural overview current.
4. **Regenerate `docs/INDEX.md` with `python tools/doc_indexer.py` whenever Markdown files change.**
5. **Validate changes with** `pre-commit run --files <changed_files>` **before committing.**
6. **Use traceable commit messages** that capture the rationale for changes and reference affected documents.

