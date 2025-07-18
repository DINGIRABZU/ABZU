from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

# Default configuration file path
DEFAULT_CONFIG = Path(__file__).resolve().parent / "source_paths.json"


def load_config(config_file: Path = DEFAULT_CONFIG) -> List[Path]:
    """Return a list of Path objects from a JSON config file."""
    if not config_file.exists():
        return []
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception:
        return []
    paths = []
    for p in data.get("source_paths", []):
        try:
            path = Path(p)
            if not path.is_absolute():
                # Resolve paths relative to the configuration file's location
                path = (config_file.parent / path).resolve()

            paths.append(path)
        except Exception:
            continue
    return paths


def load_sources(config_file: Path = DEFAULT_CONFIG) -> Dict[str, str]:
    """Load Markdown files from directories listed in the config."""
    texts: Dict[str, str] = {}
    for path in load_config(config_file):
        if not path.exists():
            continue
        for md_file in sorted(path.glob("*.md")):
            try:
                texts[md_file.name] = md_file.read_text(encoding="utf-8")
            except Exception:
                # Skip unreadable files
                continue
    return texts


def list_markdown_files(config_file: Path = DEFAULT_CONFIG) -> List[str]:
    """Return a list of Markdown file paths specified by the config."""
    files: List[str] = []
    for path in load_config(config_file):
        if not path.exists():
            continue
        files.extend(str(p) for p in sorted(path.glob("*.md")))
    return files
