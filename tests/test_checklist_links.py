import pathlib


CHECKLIST_DOC = pathlib.Path("docs/contributor_checklist.md")
REFERENCING_DOCS = [
    pathlib.Path("docs/The_Absolute_Protocol.md"),
    pathlib.Path("docs/operator_interface_GUIDE.md"),
]
INDEX_PATH = pathlib.Path("docs/INDEX.md")


def test_documents_exist():
    assert CHECKLIST_DOC.exists()
    for doc in REFERENCING_DOCS:
        assert doc.exists(), f"missing {doc}"


def test_docs_listed_in_index():
    index_text = INDEX_PATH.read_text()
    for doc in [CHECKLIST_DOC, *REFERENCING_DOCS]:
        assert doc.name in index_text, f"{doc.name} not in INDEX.md"


def test_checklist_linked_in_docs():
    for doc in REFERENCING_DOCS:
        text = doc.read_text()
        assert (
            CHECKLIST_DOC.name in text
        ), f"{doc} does not link to contributor checklist"
