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
8. **When bumping component or dependency versions:** update the relevant entries in
   `requirements.txt` and lockfiles, run `python scripts/validate_components.py` to ensure
   versions align, then execute `docs/build_docs.sh` to regenerate indexes (documentation index,
   API docs, component status) and verify links. Finally, run `python scripts/validate_docs.py`
   to confirm registry versions and cross-links remain in sync.
9. **Run `python scripts/verify_docs_up_to_date.py`** to confirm the doctrine index timestamps and
   feature references are current before submitting a pull request.

10. **Run `python scripts/check_connectors.py`** whenever files in `connectors/` or related modules change. The script fails on placeholder markers or missing MCP adoption. Every connector update must also refresh the corresponding documentation with protocol and heartbeat details.

