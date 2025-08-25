# ADR 0001: Use FAISS for Vector Search

Date: 2024-11-25

## Status
Accepted

## Context
The system requires efficient nearest-neighbor search to retrieve related memories and embeddings. Several libraries exist for high-dimensional similarity search including Elasticsearch, Annoy, and FAISS.

## Decision
Use Facebook AI Similarity Search (FAISS) as the primary vector index. FAISS offers state-of-the-art performance, GPU acceleration, and flexible indexing strategies suited to large-scale embedding retrieval.

## Consequences
* Adds a dependency on the FAISS library and its native extensions.
* Requires building or installing FAISS-compatible binaries for target platforms.
* Provides fast similarity queries and scalable index options for future growth.
