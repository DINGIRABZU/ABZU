#!/usr/bin/env python3
"""Validate Markdown links for broken or outdated targets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib import error, request

__version__ = "0.1.0"

LINK_RE = re.compile(
    r"!\[[^\]]*\]\(([^)]+)\)|\[[^\]]*\]\(([^)]+)\)|<((?:https?|ftp)://[^>]+)>"
)


def extract_links(text: str) -> list[str]:
    links: list[str] = []
    for match in LINK_RE.findall(text):
        link = match[0] or match[1] or match[2]
        if not link:
            continue
        # strip optional titles after whitespace
        links.append(link.split()[0])
    return links


def check_http(url: str) -> tuple[bool, str]:
    req = request.Request(url, method="HEAD")
    try:
        with request.urlopen(req, timeout=5) as resp:
            status = resp.status
    except error.HTTPError as e:  # pragma: no cover - network errors
        status = e.code
    except Exception as e:  # pragma: no cover - network errors
        return False, str(e)
    if 300 <= status < 400:
        return False, f"redirects with status {status}"
    if status >= 400:
        return False, f"status {status}"
    return True, ""


def check_local(link: str, base: Path) -> tuple[bool, str]:
    target = link.split("#", 1)[0]
    full = (base / target).resolve()
    if full.exists():
        return True, ""
    return False, "missing file"


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    base = path.parent
    for link in extract_links(text):
        if link.startswith("http://") or link.startswith("https://"):
            ok, reason = check_http(link)
        elif link.startswith("#"):
            continue
        else:
            ok, reason = check_local(link, base)
        if not ok:
            errors.append(f"{path}: {link} -> {reason}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    all_errors: list[str] = []
    for file in args.files:
        if file.suffix.lower() != ".md":
            continue
        all_errors.extend(validate_file(file))
    for err in all_errors:
        print(err)
    return 1 if all_errors else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
