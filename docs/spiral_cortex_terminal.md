# Spiral Cortex Terminal

`spiral_cortex_terminal.py` provides a small command line interface for exploring
`data/cortex_memory_spiral.jsonl`. The helper script `spiral_cortex_terminal.sh`
invokes the Python module from the repository root.

```
./spiral_cortex_terminal.sh [OPTIONS]
```

## Options

- `--query KEY=VAL`  Filter memory entries by decision fields. Multiple pairs may
  be supplied.
- `--dreamwalk`      Output entries sequentially with a short delay to simulate a
  dreamlike scroll.
- `--stats`          Display emotion and event statistics and print a suggested
  archetype shift when one is detected.
- `--limit N`        Limit the number of entries considered. Defaults to all.

## Examples

Show the last five joyful events:

```
./spiral_cortex_terminal.sh --query emotion=joy --limit 5
```

Wander through the most recent twenty records:

```
./spiral_cortex_terminal.sh --dreamwalk --limit 20
```

View aggregated emotion counts and any recommended archetype change:

```
./spiral_cortex_terminal.sh --stats
```
