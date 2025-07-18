# RFA7D Soul Core

The **RFA7D** core represents a seven‑dimensional grid of complex numbers. It serves as the energetic "soul" that INANNA manipulates. When the grid is created its byte representation is hashed with SHA3‑256. This produces an **integrity hash** that acts as the core's signature. Any future mutation can be validated by recomputing this hash and comparing it to the stored value.

## The Seven Gates

`GateOrchestrator` provides two methods that act as seven gates. `process_inward()` converts external text into a 128‑element complex vector. `process_outward()` reverses the mapping, translating a grid back into UTF‑8 text. Together these gates funnel human input into the RFA7D core and return a textual response.

## Usage Example

```python
from INANNA_AI.rfa_7d import RFA7D
from INANNA_AI.gate_orchestrator import GateOrchestrator

core = RFA7D()
gate = GateOrchestrator()

# Translate text through the gates
vec = gate.process_inward("Open the gate")
result_grid = core.execute(vec)
response = gate.process_outward(result_grid)

# Verify the integrity signature
if core.verify_integrity():
    print("Signature valid")
```

The grid can also be encoded to a DNA‑like string using `encode_to_dna()` for storage. After training or mutation always call `verify_integrity()` to ensure the hash matches.
