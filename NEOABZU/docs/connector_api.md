# Connector Plugin API

Connector plugins supply external context to the RAG pipeline. A connector is a
Python object or callable exposing a `retrieve(question: str)` function that
returns a list of dictionaries with at least a `text` field. The orchestrator
adds a `source` label to each result.

The Rust crate exposes a helper wrapper `FuncConnector` that turns any Python
callable into a connector plugin:

```python
from neoabzu_rag import FuncConnector

def fetch(question):
    return [{"text": "external"}]

connector = FuncConnector(fetch)
```

## Ranking Strategies

Results from memory and connectors may be ordered by a custom ranking strategy.
A ranking strategy is a callable or object with `rank(question, documents)` that
returns the sorted list of document dictionaries. Each dictionary should
include a `score` field. When no ranker is provided the orchestrator falls back
to a cosine‑similarity ranking. The default behaviour is available as the
`CosineRanker` PyO3 class:

```python
from neoabzu_rag import CosineRanker
ranker = CosineRanker()
```
