# Monitoring

The application writes JSON-formatted logs to `logs/INANNA_AI.log`. The file
rotates when it reaches roughly 10 MB, keeping seven backups
(`INANNA_AI.log.1`, `INANNA_AI.log.2`, ...).

Interactions with the corpus memory are stored separately in
`data/interactions.jsonl`. Entries are rotated when the log exceeds about 1 MB
and up to five backups are retained (`interactions.jsonl.1`,
`interactions.jsonl.2`, ...).

## Tailing logs

```bash
tail -F logs/INANNA_AI.log
```

Use `tail -F` to follow the active log file across rotations. The output uses
JSON, making it easy to filter with tools such as `jq`:

```bash
tail -F logs/INANNA_AI.log | jq '.duration? // empty'
```

## Log fields

Several JSON fields are emitted by the system:

- `symbols` and `emotion` from `invocation_engine.invoke`.
- `ritual` from `invocation_engine.invoke_ritual`.
- `path` and `method` for HTTP requests handled by the FastAPI middleware.
- `duration` in seconds for any of the above operations.

Corpus memory interaction records include:

- `timestamp` – UTC time when the interaction was logged.
- `input` – user input text.
- `intent` – parsed intent dictionary.
- `result` – resulting state or metadata.
- `outcome` – textual summary of the result.
- `emotion` – optional emotion detected or supplied.
- `source_type`, `genre`, `instrument` – optional music metadata.
- `feedback` and `rating` – optional evaluation details.

## Inspecting interaction logs

View recent corpus memory entries and pretty-print them with `jq`:

```bash
head -n 20 data/interactions.jsonl | jq .
```

Follow the file across rotations to watch interactions as they occur:

```bash
tail -F data/interactions.jsonl | jq '.input'
```

## Timing metrics

Latency histograms are exported via Prometheus:

- `invocation_duration_seconds` – pattern invocation latency.
- `ritual_invocation_duration_seconds` – ritual lookup latency.
- `http_request_duration_seconds` – FastAPI request latency labelled by path and method.

All timings use `time.perf_counter()`. Higher values indicate slower operations
and can highlight performance bottlenecks.

