from __future__ import annotations

import pathlib

import pytest

from scripts.verify_doctrine import verify_doctrine


def _setup_docs(root: pathlib.Path, protocol_text: str, index_text: str) -> None:
    docs = root / "docs"
    (docs / "testing").mkdir(parents=True)
    (docs / "The_Absolute_Protocol.md").write_text(protocol_text)
    (docs / "blueprint_spine.md").write_text("blueprint")
    (docs / "INDEX.md").write_text(index_text)
    (docs / "error_registry.md").write_text("errors")
    (docs / "testing" / "failure_inventory.md").write_text("failures")


def test_verify_doctrine_pass(tmp_path: pathlib.Path) -> None:
    protocol_text = "Before touching any code, read [blueprint_spine.md](blueprint_spine.md) three times."
    index_text = "The_Absolute_Protocol.md\nblueprint_spine.md\n"
    _setup_docs(tmp_path, protocol_text, index_text)
    verify_doctrine(tmp_path)


def test_verify_doctrine_fail(tmp_path: pathlib.Path) -> None:
    protocol_text = "Read blueprint once."
    index_text = "The_Absolute_Protocol.md\n"
    _setup_docs(tmp_path, protocol_text, index_text)
    with pytest.raises(SystemExit):
        verify_doctrine(tmp_path)
