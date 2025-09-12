# Contributor Guide

An overview of commit message conventions for contributors.

## Commit Message Format

All commits must follow the pattern:

```
feat(scope): did X on Y to obtain Z, expecting behavior B
```

- **scope** – identifier for the affected area.
- **X** – action performed.
- **Y** – target of the action.
- **Z** – result produced.
- **B** – expected behavior after the change.

- Write **X** in present tense after "did".

Example:

```
feat(api): did bump on rate limiter to obtain faster throughput, expecting behavior stable requests
```

This structure keeps history self-explanatory and traceable.
