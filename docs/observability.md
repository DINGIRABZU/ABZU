# Observability

ABZU uses the [`tracing`](https://crates.io/crates/tracing) ecosystem with OpenTelemetry for
structured diagnostics.

## Instrumentation

Use the shared `neoabzu_instrumentation` crate to initialize tracing:

```rust
use neoabzu_instrumentation::init_tracing;
use tracing::{info, instrument};

#[instrument]
fn demo() {
    info!("spanning work");
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing("demo-service")?;
    demo();
    Ok(())
}
```

Each crate calls `init_tracing` in its Python module initializer so spans are
emitted when the module loads. Apply the `#[instrument]` attribute to functions
to capture arguments and emit spans.

RAZAR, Crown, and Kimicho expose a `tracing` feature flag. Enable it at build
time to wire in the hooks and emit spans:

```bash
cargo test -p neoabzu-crown --features tracing
cargo test -p neoabzu-kimicho --features tracing
```

## Exporting

The default configuration exports spans to stdout. Configure the standard
OpenTelemetry environment variables to route data to an OTLP collector.

## Shared configuration

All crates share the same tracing and metrics setup. Initialize both telemetry
systems during startup:

```rust
use neoabzu_instrumentation::init_tracing;
use metrics_exporter_prometheus::PrometheusBuilder;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing("demo-service")?;
    PrometheusBuilder::new().install_recorder()?;
    Ok(())
}
```

With the recorder installed, counters and histograms emitted from Crown, RAG,
Insight, and Vector become available at `http://localhost:9000/metrics`. Set
`OTEL_EXPORTER_OTLP_ENDPOINT` to route spans to an external collector.
