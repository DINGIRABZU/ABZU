# LLM Framework Comparison

Several open-source frameworks aim to simplify working with large language models. Below is a short overview of popular options and how they relate to this project.

## LangChain

**Pros**
- Large ecosystem of agents, chains and integrations
- Supports many vector stores and toolkits for retrieval
- Active community and extensive tutorials

**Cons**
- Can introduce heavy dependencies
- Agent abstractions add complexity

## LlamaIndex

**Pros**
- Focused retrieval and indexing components
- Easy connectors to databases and storage backends
- Lightweight compared to LangChain

**Cons**
- Smaller community
- Mostly centered on retrieval tasks

## Haystack

**Pros**
- Python toolkit for building RAG pipelines
- Good documentation and plugin system

**Cons**
- Primarily geared toward document search workflows

## Semantic Kernel

**Pros**
- Microsoft backed with C# and Python support
- Plugin approach for composing skills

**Cons**
- Less mature Python ecosystem

## Best Fit for SPIRAL_OS

LangChain already appears in the project plans as the orchestrator for multiple LLMs and tools. Its agent interface and retrieval integrations align with the intended architecture. LlamaIndex or Haystack can complement LangChain for corpus indexing, but LangChain offers the most comprehensive feature set for SPIRAL_OS overall.
