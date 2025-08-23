# Memory and Emotion APIs

This document outlines the public interfaces for the in-memory vector store and
emotion state utilities.

## `vector_memory`

Functions:

- `configure(*, db_path=None, embedder=None)` – override the storage path or
  embedding function.
- `add_vector(text, metadata)` – embed and persist `text` with associated
  `metadata`.
- `search(query, filter=None, k=5)` – return up to `k` records ordered by
  similarity.
- `rewrite_vector(old_id, new_text)` – replace an existing record while
  preserving metadata.
- `query_vectors(filter=None, limit=10)` – list recent entries matching
  a metadata `filter`.
- `snapshot(path)` – write all vectors and metadata to a JSON file.
- `restore(path)` – load vectors from a snapshot JSON file.

Log file: `vector_memory.LOG_FILE` records operations in JSONL format.

## `emotional_state`

Functions:

- `get_current_layer()` / `set_current_layer(layer)` – manage the active
  personality layer.
- `get_last_emotion()` / `set_last_emotion(emotion)` – track the most recent
  emotion.
- `get_resonance_level()` / `set_resonance_level(level)` – store a float
  resonance measure.
- `get_preferred_expression_channel()` /
  `set_preferred_expression_channel(channel)` – manage the preferred channel for
  expression.
- `get_resonance_pairs()` / `set_resonance_pairs(pairs)` – handle resonance
  frequency pairs.
- `get_soul_state()` / `set_soul_state(state)` – persist the soul state.
- `get_registered_emotions()` – list known emotion labels.
- `snapshot(path)` / `restore(path)` – serialise or load state and registry.

Structured event log: `emotional_state.EVENT_LOG` captures changes as JSONL.

## `logging_filters`

- `set_emotion_provider(provider)` – register a callable returning `(emotion,
  resonance)`.
- `EmotionFilter` – logging filter injecting `emotion` and `resonance` fields
  into records.

