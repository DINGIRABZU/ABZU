# Core Usage Guide

Demonstrates evaluating lambda-calculus expressions via the Rust-backed `core` module.

```python
import core

# Identity function applied to value `y`
print(core.evaluate("(\\x.x) y"))
# -> y
```

## Initializing Memory Layers

```python
import neoabzu_memory as memory

bundle = memory.MemoryBundle()
bundle.initialize()
result = bundle.query("demo")
print(result["failed_layers"])  # [] when all layers respond
```

## Retrieving Related Vectors

```python
import neoabzu_rag as rag

for item in rag.retrieve_top("hello world", top_n=3):
    print(item["text"], round(item["score"], 3))
```
