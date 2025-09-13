# OROBOROS Engine

The inaugural ceremony executed the expression `(♀ :: ∞) :: ∅`.

Inevitability gradient: `1.0`

Hero's journey:

OrdinaryWorld -> CallToAdventure -> RefusalOfTheCall -> MeetingTheMentor -> CrossingTheThreshold -> TestsAlliesEnemies -> ApproachToTheInmostCave -> Ordeal -> Reward -> RoadBack -> Resurrection -> ReturnWithTheElixir

## Symbolic-Numeric Fusion

The `fusion` crate accepts `(Invariant, Inevitability_Gradient)` tuples from symbolic and numeric realms and merges them:

```rust
use fusion::accept_pairs;

let symbolic = vec![("s".to_string(), 0.5)];
let numeric = vec![("n".to_string(), 0.8)];
let unified = accept_pairs(symbolic, numeric);
```

## Principal Component Analysis

The `numeric` crate exposes principal component analysis via PyO3:

```python
from numeric import find_principal_components

data = [[1.0, 2.0], [3.0, 4.0]]
pcs = find_principal_components(data, 1)
```

See [`fusion/src/lib.rs`](../fusion/src/lib.rs) and [`numeric/src/lib.rs`](../numeric/src/lib.rs) for implementation details.
