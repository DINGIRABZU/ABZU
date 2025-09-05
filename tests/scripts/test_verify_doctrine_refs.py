from __future__ import annotations

import pathlib

import pytest

from scripts.verify_doctrine_refs import verify_doctrine_refs


def _write_index(root: pathlib.Path, content: str) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "INDEX.md").write_text(content)


def test_verify_doctrine_refs_pass(tmp_path: pathlib.Path) -> None:
    index_text = (
        "The_Absolute_Protocol.md\n"
        "blueprint_spine.md\n"
        "error_registry.md\n"
        "testing/failure_inventory.md\n"
    )
    _write_index(tmp_path, index_text)
    verify_doctrine_refs(tmp_path)


def test_verify_doctrine_refs_fail(tmp_path: pathlib.Path) -> None:
    index_text = "The_Absolute_Protocol.md\n"
    _write_index(tmp_path, index_text)
    with pytest.raises(SystemExit):
        verify_doctrine_refs(tmp_path)
