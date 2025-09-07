"""Validate documentation registry versions and cross-links."""

from __future__ import annotations

__version__ = "0.1.0"

import json
import re
from pathlib import Path
import sys

REGISTRY_PATH = Path("docs/chakra_versions.json")
DOC_PATH = Path("docs/chakra_koan_system.md")


def load_registry() -> tuple[dict, dict[str, int]]:
    """Return registry data and line numbers for each chakra key."""
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    data = json.loads("\n".join(lines))
    line_map: dict[str, int] = {}
    pattern = re.compile(r'"([^"\\]+)":\s*{')
    for idx, line in enumerate(lines, start=1):
        match = pattern.search(line)
        if match:
            key = match.group(1)
            line_map[key] = idx
    return data, line_map


def parse_doc() -> tuple[dict[str, tuple[str, int]], set[str]]:
    """Extract versions and anchors from the koan document."""
    versions: dict[str, tuple[str, int]] = {}
    anchors: set[str] = set()
    current: str | None = None
    anchor_re = re.compile(r'<a id="([^"]+)"></a>')
    version_re = re.compile(
        r"\*Version:\s+\[(?P<ver>[0-9.]+)\]\(chakra_versions\.json#L(?P<line>\d+)\)\*"
    )
    for line in DOC_PATH.read_text(encoding="utf-8").splitlines():
        anchor_match = anchor_re.search(line)
        if anchor_match:
            current = anchor_match.group(1)
            anchors.add(current)
            continue
        if current:
            version_match = version_re.search(line)
            if version_match:
                versions[current] = (
                    version_match.group("ver"),
                    int(version_match.group("line")),
                )
                current = None
    return versions, anchors


def main() -> int:
    if not REGISTRY_PATH.exists() or not DOC_PATH.exists():
        print("Required documentation files missing", file=sys.stderr)
        return 1

    registry, line_map = load_registry()
    doc_versions, anchors = parse_doc()
    ok = True
    for chakra, info in registry.items():
        if chakra == "meta":
            continue
        expected_version = info.get("version")
        koan = info.get("koan", "")
        anchor = koan.split("#", 1)[1] if "#" in koan else chakra
        doc_info = doc_versions.get(anchor)
        if not doc_info:
            print(f"Missing version entry for {chakra} in {DOC_PATH}", file=sys.stderr)
            ok = False
            continue
        version, linked_line = doc_info
        if version != expected_version:
            print(
                f"{chakra} version mismatch: "
                f"registry {expected_version} != doc {version}",
                file=sys.stderr,
            )
            ok = False
        registry_line = line_map.get(chakra)
        if registry_line != linked_line:
            print(
                f"{chakra} link outdated: doc points to L{linked_line}, "
                f"registry at L{registry_line}",
                file=sys.stderr,
            )
            ok = False
        if anchor not in anchors:
            print(
                f"{chakra} koan anchor '#{anchor}' not found in {DOC_PATH}",
                file=sys.stderr,
            )
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
