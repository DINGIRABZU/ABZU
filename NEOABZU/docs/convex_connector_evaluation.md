# Convex Connector Evaluation

## Overview
This note summarizes the performance and cost characteristics observed while testing Convex as an agent log store connected through the Pipecat/videocall-rs and Vanna connectors.

## Benchmark setup
- **Pipecat/videocall-rs** handled duplex audio/video streams for 50 concurrent sessions.
- **Vanna** translated 200 analytical queries into SQL against the Convex-backed store.
- All tests executed on a single `m6i.large` instance.

## Performance
- Pipecat/videocall-rs sustained ~45 sessions before jitter exceeded 50 ms.
- Vanna processed the query batch in 4.2 s with mean latency of 21 ms per query.

## Cost
- Convex storage/compute for the test window totaled approximately $0.19.
- Pipecat/videocall-rs bandwidth usage equated to ~$0.05.
- Vanna query translation consumed ~$0.02 of billable tokens.

## Integration timing
Full integration is deferred until Crown, Kimicho, RAG, and Insight reach stable parity. The connectors remain isolated for ongoing experimentation.

## Next steps
1. Expand tests to multi-region Convex deployments.
2. Automate cost telemetry collection in CI.
3. Re-evaluate after parity milestone to schedule merge.

