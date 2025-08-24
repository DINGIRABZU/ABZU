# Monitoring

The application writes JSON-formatted logs to `logs/INANNA_AI.log` and rotates the file when it grows beyond 1 MB. Each rotated copy is suffixed with a number (for example, `INANNA_AI.log.1`).

## Tailing logs

```bash
tail -F logs/INANNA_AI.log
```

Use `tail -F` to follow the active log file across rotations. The output uses JSON, making it easy to filter with tools such as `jq`:

```bash
tail -F logs/INANNA_AI.log | jq '.duration? // empty'
```

## Timing metrics

Two parts of the system emit a `duration` field measured in seconds using `time.perf_counter()`:

- `invocation_engine.invoke` reports how long pattern matching and callbacks take.
- The FastAPI server middleware logs the processing time for every HTTP request along with its path and method.

Higher durations indicate slower operations. Watching these metrics helps identify performance bottlenecks.
