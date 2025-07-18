import sys
from pathlib import Path
import types
import re

sys.modules.setdefault("requests", types.ModuleType("requests"))
bs4_mod = types.ModuleType("bs4")
bs4_mod.BeautifulSoup = lambda *a, **k: None
sys.modules.setdefault("bs4", bs4_mod)
sys.modules.setdefault("numpy", types.ModuleType("numpy"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.learning import project_gutenberg as pg


def test_search_parses_results(monkeypatch):
    html = """
    <li class='booklink'>
      <a href='/ebooks/123'></a>
      <span class='title'>Title A</span>
    </li>
    <li class='booklink'>
      <a href='/ebooks/456'></a>
      <span class='title'>Title B</span>
    </li>
    """
    class DummyResp:
        text = html
        def raise_for_status(self):
            return None

    dummy_req = types.ModuleType("requests")
    dummy_req.get = lambda *a, **k: DummyResp()
    dummy_req.utils = types.SimpleNamespace(quote=lambda q: q)
    monkeypatch.setattr(pg, "requests", dummy_req)

    class DummySoup:
        def __init__(self, text):
            self.text = text

        def select(self, selector):
            matches = re.findall(r"<a href='/ebooks/(\d+)'></a>\s*<span class='title'>([^<]+)", self.text)
            books = []
            for book_id, title in matches:
                class Book:
                    def __init__(self, bid, t):
                        self.bid = bid
                        self.title = t

                    def find(self, tag, href=False, class_=None):
                        if tag == "a" and href:
                            return {"href": f"/{self.bid}"}
                        if tag == "span" and class_ == "title":
                            return types.SimpleNamespace(get_text=lambda strip=True: self.title)
                        return None

                books.append(Book(book_id, title))
            return books

    monkeypatch.setattr(pg, "BeautifulSoup", lambda text, parser: DummySoup(text))
    results = pg.search("foo", max_results=2)
    assert results == [("123", "Title A"), ("456", "Title B")]


def test_download_tries_patterns(monkeypatch, tmp_path):
    calls = []
    def dummy_download(url, dest):
        calls.append(url)
        if url.endswith("-0.txt"):
            raise RuntimeError("fail")
        dest.write_text("content", encoding="utf-8")
        return dest
    monkeypatch.setattr(pg, "_download_file", dummy_download)
    path = pg.download("789", dest_dir=tmp_path)
    assert path.read_text() == "content"
    assert calls[0].endswith("789-0.txt")
    assert any(url.endswith(".txt") for url in calls)


def test_chunk_respects_token_limit():
    text = " ".join(str(i) for i in range(10))
    chunks = pg.chunk(text, max_tokens=3)
    assert all(len(c.split()) <= 3 for c in chunks)
    assert " ".join(chunks) == text


def test_ingest_downloads_and_embeds(monkeypatch, tmp_path):
    monkeypatch.setattr(pg, "search", lambda q, max_results=1: [("1", "Book")])

    raw = tmp_path / "book.txt"
    raw.write_text("alpha beta gamma", encoding="utf-8")
    monkeypatch.setattr(pg, "download", lambda book_id, dest_dir=None: raw)
    monkeypatch.setattr(pg, "clean_text", lambda path: path)

    seen = {}

    class DummyModel:
        def __init__(self, name):
            seen["model"] = name

        def encode(self, texts, convert_to_numpy=True):
            seen["texts"] = list(texts)
            class Vec(list):
                def tolist(self):
                    return list(self)

            return [Vec([0.0]) for _ in texts]

    class DummyCollection:
        def add(self, ids=None, embeddings=None, metadatas=None, documents=None):
            seen["ids"] = ids
            seen["metadatas"] = metadatas
            seen["docs"] = documents

    monkeypatch.setattr(pg, "SentenceTransformer", DummyModel)
    monkeypatch.setattr(pg.corpus_memory, "create_collection", lambda: DummyCollection())

    pg.ingest("query")

    assert seen["model"] == "all-MiniLM-L6-v2"
    assert seen["docs"] == ["alpha beta gamma"]
    assert seen["metadatas"] == [{"book_id": "1", "title": "Book"}]
    assert seen["ids"][0].startswith("1:")
