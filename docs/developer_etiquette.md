# Developer Etiquette

This guide outlines collaboration practices for contributors.

## Commit Messages
- Use the imperative mood: "add feature" not "added".
- Keep the first line under 50 characters.
- Provide context in the body wrapped at 72 characters.
- Reference related issues or tickets when relevant.

## Branch Naming
- Prefix with a category such as `feat/`, `fix/`, or `docs/`.
- Use lowercase with hyphens: `feat/add-music-caching`.
- Keep names concise and descriptive.

## Documentation in Pull Requests
- Update all relevant docs alongside code changes.
- Mention documentation updates in the PR description with relative links.
- Cite issue numbers with `Fixes #123` when applicable.

## Code Examples

### Docstring
```python
    def add(a: int, b: int) -> int:
        """Return the sum of two integers."""
        return a + b
```

### Logging
```python
    import logging
    logger = logging.getLogger(__name__)

    def process(item: str) -> None:
        logger.info("Processing item %s", item)
```

### Error Handling
```python
    def read(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as exc:
            logger.error("Failed to read %s", path, exc_info=exc)
            raise
```

## Additional Resources
- [Developer Onboarding](developer_onboarding.md)
- [Development Checklist](development_checklist.md)
