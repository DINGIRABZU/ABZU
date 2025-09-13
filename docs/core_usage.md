# Core Usage

Install the compiled wheels:

```bash
pip install neoabzu
```

Import modules that mirror the original APSU APIs:

```python
from neoabzu import core, memory, fusion, persona, crown, rag, vector, numeric
```

Each submodule exposes the Rust-accelerated functions directly, e.g.:

```python
result = core.evaluate("(λx.x)(42)")
items = rag.retrieve_top("meaning", 3)
```
