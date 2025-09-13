# Core Usage Guide

Demonstrates evaluating lambda-calculus expressions via the Rust-backed `core` module.

## Installation

```bash
pip install neoabzu
```

## Evaluating Expressions

```python
from neoabzu import core

# Identity function applied to value `y`
print(core.evaluate("(\\x.x) y"))
# -> y
```

## Hero Journey Stage Markers

When tracing is enabled, evaluation reveals the Hero's Journey progression:

```text
stage=OrdinaryWorld
stage=RefusalOfTheCall token=a
stage=CrossingTheThreshold token=b
stage=ApproachToTheInmostCave token=c
stage=Reward token=d
stage=ReturnWithTheElixir token=e
```

## Initializing Memory Layers

```python
from neoabzu import memory

bundle = memory.MemoryBundle()
bundle.initialize()
result = bundle.query("demo")
print(result["failed_layers"])  # [] when all layers respond
```

## Retrieving Related Vectors

```python
from neoabzu import vector

for text, score in vector.search("hello world", top_n=3):
    print(text, round(score, 3))
```

## Computing Principal Components

```python
from neoabzu import numeric

data = [[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]]
print(numeric.find_principal_components(data, n_components=1))
```

## Computing Cosine Similarity

```python
from neoabzu import numeric

a = [1.0, 0.0, 1.0]
b = [0.0, 1.0, 1.0]
print(numeric.cosine_similarity(a, b))
```
