# Cortex Memory Search

The `memory.cortex` module stores spiral decisions as JSON lines under
`data/cortex_memory_spiral.jsonl`. Each entry may contain a list of semantic
`tags` which are indexed for fast lookup. A companion full‑text index tokenizes
these tags allowing substring queries.

## Recording

```python
from memory import cortex

cortex.record_spiral(node, {"action": "run", "tags": ["fast runner"]})
```

## Querying

Use exact tag matching:

```python
cortex.query_spirals(tags=["fast runner"])
```

Full‑text search splits tags into tokens so the above entry is also retrieved
with:

```python
cortex.query_spirals(text="runner")
```

Multiple queries can be issued concurrently with `query_spirals_concurrent`:

```python
queries = [{"tags": ["fast"]}, {"text": "runner"}]
results = cortex.query_spirals_concurrent(queries)
```

Each element in `results` corresponds to the associated query dict.

The tag index is persisted to `data/cortex_memory_index.json` and is rebuilt
whenever entries are pruned.
