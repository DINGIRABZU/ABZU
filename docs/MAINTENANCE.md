# Maintenance

## Link Validation

Use `scripts/validate_links.py` to scan Markdown files for links that redirect or fail.
Pre-commit runs the script on staged Markdown files, and CI checks the entire repository.

### Manual usage

```bash
python scripts/validate_links.py path/to/file.md
```

The command exits with a non-zero status if any broken or outdated links are found.
