#!/usr/bin/env python3
"""Fail CI when crates change without doc or test updates."""
import os
import subprocess
import sys

BASE = os.environ.get("GITHUB_BASE_REF", "main")

changed = subprocess.check_output(
    ["git", "diff", "--name-only", f"origin/{BASE}...HEAD"],
    text=True,
).splitlines()
changed_set = set(changed)

crate_paths = ("crown/", "NEOABZU/kimicho/")
crate_changed = any(any(p.startswith(cp) for cp in crate_paths) for p in changed_set)

docs_required = {
    "docs/The_Absolute_Protocol.md",
    "docs/system_blueprint.md",
    "docs/blueprint_spine.md",
    "docs/NEOABZU_spine.md",
    "docs/migration_crosswalk.md",
    "docs/index.md",
    "docs/INDEX.md",
}
if crate_changed and not docs_required.issubset(changed_set):
    sys.stderr.write(
        "crate changes require blueprint, protocol, and index document updates\n"
    )
    sys.exit(1)

# If crate source files changed ensure a corresponding test file changed
code_changes = [
    p
    for p in changed_set
    if any(p.startswith(cp) for cp in crate_paths)
    and p.endswith(".rs")
    and "/tests/" not in p
]
if code_changes:
    if not any(p.startswith(cp + "tests/") for p in changed_set for cp in crate_paths):
        sys.stderr.write("crate changes require test updates\n")
        sys.exit(1)
