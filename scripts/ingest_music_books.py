from __future__ import annotations

"""Ingest music theory books into the vector memory."""

import argparse
from pathlib import Path
from typing import List, Dict

import vector_memory

try:  # pragma: no cover - optional dependency
    from unstructured.partition.text import partition_text
    from unstructured.partition.epub import partition_epub
except Exception:  # pragma: no cover - optional dependency
    partition_text = None  # type: ignore
    partition_epub = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None  # type: ignore


def _read_pdf(path: Path) -> str:
    if pdfplumber is None:
        raise RuntimeError("pdfplumber library not installed")
    with pdfplumber.open(str(path)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _read_epub(path: Path) -> str:
    if partition_epub is None:
        raise RuntimeError("unstructured library not installed")
    elements = partition_epub(filename=str(path))
    return "\n".join(e.text or "" for e in elements)


def _read_txt(path: Path) -> str:
    if partition_text is None:
        raise RuntimeError("unstructured library not installed")
    elements = partition_text(filename=str(path))
    return "\n".join(e.text or "" for e in elements)


def _chunk(text: str, max_words: int = 200) -> List[str]:
    words = text.split()
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]


def ingest(path: Path, metadata: Dict[str, str]) -> None:
    ext = path.suffix.lower()
    if ext == ".pdf":
        text = _read_pdf(path)
    elif ext == ".epub":
        text = _read_epub(path)
    elif ext == ".txt":
        text = _read_txt(path)
    else:  # pragma: no cover - unsupported type
        raise RuntimeError(f"unsupported file type: {path.suffix}")

    pieces = _chunk(text)
    meta = dict(metadata)
    meta["SOURCE_TYPE"] = ext.lstrip(".").upper()
    meta["SOURCE_PATH"] = str(path)
    for chunk in pieces:
        vector_memory.add_vector(chunk, meta)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingest music books into memory")
    parser.add_argument("files", nargs="+", help="Paths of books to ingest")
    parser.add_argument("--genre", default="", help="Genre label")
    parser.add_argument("--year", default="", help="Publication year")
    parser.add_argument("--culture", default="", help="Culture of origin")
    parser.add_argument("--instruments", default="", help="Comma-separated instruments")
    args = parser.parse_args(argv)

    meta = {
        "GENRE": args.genre,
        "YEAR": args.year,
        "CULTURE": args.culture,
        "INSTRUMENTS": args.instruments,
    }

    for file in args.files:
        ingest(Path(file), meta)
        print(f"Ingested {file}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()

