# ADR 0002: Prefer asyncio over Threads

Date: 2024-11-25

## Status
Accepted

## Context
Concurrent tasks such as IO-bound model requests and network interactions need a structured approach. Traditional threading introduces complexity and overhead, while asynchronous programming can efficiently handle many concurrent operations.

## Decision
Adopt Python's `asyncio` framework as the default concurrency model. Components interacting with external services or performing IO should expose asynchronous interfaces and run within the event loop.

## Consequences
* Requires wrapping or offloading blocking calls to thread or process executors.
* Simplifies orchestration by avoiding explicit thread management.
* Enables high concurrency with lower resource usage compared to spawning many threads.
