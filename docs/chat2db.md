# Chat2DB Interface

## Purpose
Chat2DB connects conversational agents to persistent storage. It logs transcripts,
feedback and model metrics in a lightweight SQLite database while maintaining a
vector index for semantic search. The bridge lets the system recall prior
interactions and fetch relevant context during dialogue.

## Architecture
- **Relational Layer:** [INANNA_AI/db_storage.py](../INANNA_AI/db_storage.py)
  initializes tables for interactions, feedback and benchmarks and exposes
  helpers such as `save_interaction` and `fetch_feedback`.
- **Vector Layer:** [spiral_vector_db/__init__.py](../spiral_vector_db/__init__.py)
  wraps a ChromaDB collection for storing and querying text embeddings via
  `insert_embeddings` and `query_embeddings`.
- Both layers share a common path under `data/` so deployments can snapshot or
  restore the complete conversation state.

## Usage
1. Initialize the stores:
   ```python
   from INANNA_AI import db_storage
   from spiral_vector_db import init_db

   db_storage.init_db()
   init_db()  # sets up the Chroma collection
   ```
2. Record a message:
   ```python
   db_storage.save_interaction("hello", "neutral", "response.wav")
   ```
3. Add and query embeddings:
   ```python
   from spiral_vector_db import insert_embeddings, query_embeddings

   insert_embeddings([{"text": "hello world"}])
   matches = query_embeddings("hello")
   ```
The interface is stateless; components import these helpers as needed. See the
[system blueprint](system_blueprint.md#chat2db-interface) for how Chat2DB fits in
the overall stack.
