# Installation Profiles

This project provides several installation profiles using optional dependencies
defined in `pyproject.toml`.

## Minimal

Install only the core requirements:

```bash
pip install -e .
```

## Audio

Include audio features:

```bash
pip install -e .[audio]
```

## Vision

Include vision features:

```bash
pip install -e .[vision]
```

## Full

Install all available extras:

```bash
pip install -e .[audio,vision,llm,ml,web,network]
```

