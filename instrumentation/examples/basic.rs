use neoabzu_instrumentation::init_tracing;
use tracing::info;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing("basic-example")?;
    info!("example span");
    Ok(())
}
