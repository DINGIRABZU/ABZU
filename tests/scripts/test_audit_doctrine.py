from __future__ import annotations

import pathlib

import pytest

from scripts.audit_doctrine import audit_doctrine


def _setup_docs(
    root: pathlib.Path,
    protocol_text: str,
    index_text: str,
    error_text: str = "errors",
    failure_text: str = "failures",
) -> None:
    docs = root / "docs"
    (docs / "testing").mkdir(parents=True)
    (docs / "The_Absolute_Protocol.md").write_text(protocol_text)
    (docs / "blueprint_spine.md").write_text("blueprint")
    (docs / "INDEX.md").write_text(index_text)
    (docs / "error_registry.md").write_text(error_text)
    (docs / "testing" / "failure_inventory.md").write_text(failure_text)


def test_audit_doctrine_pass(tmp_path: pathlib.Path) -> None:
    protocol_text = "Before touching any code, read [blueprint_spine.md](blueprint_spine.md) three times."
    index_text = (
        "The_Absolute_Protocol.md\n"
        "blueprint_spine.md\n"
        "error_registry.md\n"
        "testing/failure_inventory.md\n"
    )
    _setup_docs(tmp_path, protocol_text, index_text)
    audit_doctrine(tmp_path)


def test_audit_doctrine_fail(tmp_path: pathlib.Path) -> None:
    protocol_text = "Read blueprint once."
    index_text = "The_Absolute_Protocol.md\n"
    _setup_docs(tmp_path, protocol_text, index_text, error_text="")
    with pytest.raises(SystemExit):
        audit_doctrine(tmp_path)
