# Core Usage Guide

Demonstrates evaluating lambda-calculus expressions via the Rust-backed `core` module.

```python
import core

# Identity function applied to value `y`
print(core.evaluate("(\\x.x) y"))
# -> y
```
