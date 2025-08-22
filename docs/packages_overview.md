# Package Overview

This guide summarises the major Python packages in the ABZU codebase and how they are typically used.

## INANNA_AI

The `INANNA_AI` package contains modules for ritual analysis, memory systems and network utilities. The command line agent in [`INANNA_AI_AGENT/inanna_ai.py`](../INANNA_AI_AGENT/inanna_ai.py) draws on these modules.

**Example**

```bash
python INANNA_AI_AGENT/inanna_ai.py --activate
```

Key modules:

- [`INANNA_AI/ethical_validator.py`](../INANNA_AI/ethical_validator.py) – filter prompts before they reach the models.
- [`INANNA_AI/network_utils`](../INANNA_AI/network_utils/) – packet capture and analysis tools.

## core

The `core` package hosts the language processing engines and memory interfaces used by the orchestrator.

**Example**

```python
from core.emotion_analyzer import EmotionAnalyzer

analyzer = EmotionAnalyzer()
mood = analyzer.classify("welcome")
```

Key modules:

- [`core/emotion_analyzer.py`](../core/emotion_analyzer.py) – classify mood of text.
- [`core/model_selector.py`](../core/model_selector.py) – choose an appropriate language model.
- [`core/memory_logger.py`](../core/memory_logger.py) – persist conversation events.

## dashboard

The `dashboard` package provides a Streamlit interface for monitoring usage and experiments.

**Example**

```bash
streamlit run dashboard/app.py
```

Key modules:

- [`dashboard/app.py`](../dashboard/app.py) – main Streamlit application.
- [`dashboard/usage.py`](../dashboard/usage.py) – usage reporting helpers.

## rag

`rag` implements retrieval‑augmented generation for context‑aware responses.

**Example**

```python
from rag.retriever import retrieve

results = retrieve("ocean rituals")
```

Key modules:

- [`rag/orchestrator.py`](../rag/orchestrator.py) – central coordinator for retrieval calls.
- [`rag/retriever.py`](../rag/retriever.py) – search vector memory for relevant passages.
- [`rag/music_oracle.py`](../rag/music_oracle.py) – craft musical prompts from retrieved text.

## memory

The `memory` package stores experiences and insights across multiple layers.

**Example**

```python
from memory.cortex import record_spiral

record_spiral({"event": "init"})
```

Key modules:

- [`memory/cortex.py`](../memory/cortex.py) – persistence for spiral decisions.
- [`memory/spiral_cortex.py`](../memory/spiral_cortex.py) – log and retrieve insights.
- [`memory/emotional.py`](../memory/emotional.py) – track emotional state over time.

