# Banana Rater

## Purpose
The Banana Rater scores banana quality submissions and streams the result to Nazarick agents for downstream decision making.

## Inputs
- **image**: peeled or unpeeled banana photo provided by a Nazarick servant.
- **metadata**: optional JSON blob with harvest time and origin notes.

## Outputs
- **rating**: float in `[0,1]` describing ripeness suitability.
- **notes**: free‑form string summarizing evaluation context.

## Nazarick Integration
Banana Rater posts ratings to the Nazarick event bus so agents can adjust harvesting rituals or trigger storage workflows.

## Testing
- Unit tests validate rating bounds and metadata parsing.
- Heartbeat hooks emit `banana_rater.heartbeat` after each batch to confirm liveness.

## Observability
- Tracing spans wrap each evaluation to surface latency in distributed runs.
- Heartbeat events forward to the central metrics sink for monitoring dashboards.
