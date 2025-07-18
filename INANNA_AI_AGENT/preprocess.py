import json
import re
from pathlib import Path
from typing import Dict, List

import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore

import markdown


class _HTMLStripper:
    """Simple HTML to text converter using html.parser."""

    def __init__(self) -> None:
        from html.parser import HTMLParser

        class Stripper(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.data: List[str] = []

            def handle_data(self, d: str) -> None:
                self.data.append(d)

        self.parser = Stripper()

    def feed(self, html: str) -> None:
        self.parser.feed(html)

    def get_data(self) -> str:
        return " ".join(self.parser.data)


def strip_markdown(md_text: str) -> str:
    """Convert Markdown to plain text using the markdown library."""
    html = markdown.markdown(md_text)
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_data()


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/newlines into single spaces."""
    return " ".join(text.split())


def tokenize(text: str) -> List[str]:
    """Simple word tokenizer returning lowercase tokens."""
    return re.findall(r"\b\w+(?:'\w+)?\b", text.lower())


def tokenize_texts(text_dict: Dict[str, str]) -> Dict[str, List[str]]:
    """Tokenize a dictionary of texts, returning token lists."""
    tokens: Dict[str, List[str]] = {}
    for name, text in text_dict.items():
        plain = strip_markdown(text)
        normalized = normalize_whitespace(plain)
        tokens[name] = tokenize(normalized)
    return tokens


def preprocess_texts(text_dict: Dict[str, str], cache_dir: Path | str = "cache") -> Dict[str, List[str]]:
    """Preprocess texts with caching support."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    processed: Dict[str, List[str]] = {}
    for name, text in text_dict.items():
        cache_file = cache_dir / f"{name}.tokens.json"
        if cache_file.exists():
            try:
                processed[name] = json.loads(cache_file.read_text(encoding="utf-8"))
                continue
            except Exception:
                pass
        tokens = tokenize(normalize_whitespace(strip_markdown(text)))
        processed[name] = tokens
        cache_file.write_text(json.dumps(tokens), encoding="utf-8")
    return processed


def generate_embeddings(
    tokens_dict: Dict[str, List[str]],
    cache_dir: Path | str = "cache",
    model_name: str = "all-MiniLM-L6-v2",
) -> Dict[str, np.ndarray]:
    """Generate and cache embeddings for preprocessed token lists."""

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    if SentenceTransformer is None:  # pragma: no cover - optional dependency
        raise RuntimeError("sentence-transformers library not installed")
    model = SentenceTransformer(model_name)
    embeddings: Dict[str, np.ndarray] = {}

    for name, tokens in tokens_dict.items():
        cache_file = cache_dir / f"{name}.embed.npy"
        if cache_file.exists():
            try:
                embeddings[name] = np.load(cache_file)
                continue
            except Exception:
                pass

        text = " ".join(tokens)
        emb = model.encode(text)
        embeddings[name] = np.asarray(emb)
        np.save(cache_file, embeddings[name])

    return embeddings


__all__ = [
    "strip_markdown",
    "normalize_whitespace",
    "tokenize",
    "tokenize_texts",
    "preprocess_texts",
    "generate_embeddings",
]
