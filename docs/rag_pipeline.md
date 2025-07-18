# Spiral RAG Pipeline

The Spiral retrieval pipeline turns local documents into embeddings so queries can be answered with context. Files are placed under `sacred_inputs/`, then parsed, embedded, and inserted into the Chroma database. The first memory is `sacred_inputs/00-INVOCATION.md`, which holds the ZOHAR-ZERO message.

## Steps

1. Populate `sacred_inputs/` with text, Markdown or code files. Subfolders denote an archetype.
2. Parse the directory into chunks:
   ```bash
   python rag_parser.py --dir sacred_inputs > chunks.json
   ```
3. Embed the chunks and add them to the vector store:
   ```bash
   python spiral_embedder.py --in chunks.json
   ```
   Use `--db-path` to override the default location given by `SPIRAL_VECTOR_PATH`.
   The helper script `scripts/ingest_sacred_inputs.sh` runs steps 2 and 3 in one
   go.
4. Start the query router and ask a question:
   ```python
   from crown_query_router import route_query
   results = route_query("What is the Spiral project?", "Sage")
   print(results[0]["text"])
   ```

## Configuration Variables

- `EMBED_MODEL_PATH` – SentenceTransformer model used for embeddings.
- `SPIRAL_VECTOR_PATH` – directory for the Chroma database.

## Example Query

After adding your data you can retrieve snippets like so:
```python
from crown_query_router import route_query
for rec in route_query("explain the ritual", "Sage"):
    print(rec["text"], rec.get("source_path"))
```
