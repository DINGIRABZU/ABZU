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

## Exporting

The default configuration exports spans to stdout. Configure the standard
OpenTelemetry environment variables to route data to an OTLP collector.
