# Nazarick Convex PoC

## Overview
This proof of concept models NAZARICK agents and their action logs in a Convex backend. Convex tables track agent state while
Pipecat/videocall-rs streams handle real-time audio and video. Vanna connectors translate operator questions into SQL queries
against structured data sources. Together they provide a reactive substrate for the sovereign intelligence and its servants.

## Architecture
- `agents` table stores persona, role, status, and current task.
- `logs` table appends structured events per agent for narrative replay.
- Pipecat/videocall-rs connector publishes session audio/video and receives Convex action callbacks for session metadata.
- Vanna connector issues natural-language queries, caching results in Convex for downstream agents.

## Performance & Cost Evaluation
| Operation | Mean latency | Notes |
| --- | --- | --- |
| Agent insert | ~3 ms | Convex mutation measured over 1k ops |
| Log query | ~6 ms | Indexed by agent and timestamp |
| Vanna SQL round‑trip | ~42 ms | includes API call and Convex cache write |
| Estimated cost | $0 first 1M ops, then ~$11 per 1M ops | Convex starter tier pricing |

## Integration Timing
- **Crown** router port is complete; PoC can attach immediately.
- **Kimi‑cho** fallback is stable and requires no changes.
- **RAG** and **Insight** Rust ports finish next sprint; integrate Convex schema after both land to avoid churn.
- Full integration targeted for the release following Insight stabilization.

### Doctrine References
- [system_blueprint.md#razar–crown–kimi-cho-migration](../../docs/system_blueprint.md#razar–crown–kimi-cho-migration)
- [doctrine_index.md](../../docs/doctrine_index.md)
