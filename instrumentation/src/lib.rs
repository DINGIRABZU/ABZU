use opentelemetry::{global, trace::TracerProvider, KeyValue};
use opentelemetry_sdk::{trace as sdktrace, Resource};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Initialize global tracing and OpenTelemetry pipeline.
///
/// # Examples
/// ```
/// use neoabzu_instrumentation::init_tracing;
/// use tracing::info;
///
/// fn main() -> Result<(), Box<dyn std::error::Error>> {
///     init_tracing("demo")?;
///     info!("tracing ready");
///     Ok(())
/// }
/// ```
pub fn init_tracing(service_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    let provider = sdktrace::TracerProvider::builder()
        .with_config(sdktrace::Config::default().with_resource(Resource::new(vec![
            KeyValue::new("service.name", service_name.to_string()),
        ])))
        .build();
    let tracer = provider.tracer(service_name.to_string());
    global::set_tracer_provider(provider);
    let otel = tracing_opentelemetry::layer().with_tracer(tracer);
    let fmt = tracing_subscriber::fmt::layer();
    tracing_subscriber::registry().with(fmt).with(otel).try_init()?;
    Ok(())
}
