use neoabzu_memory::MemoryBundle;
use pyo3::prelude::*;

fn main() -> PyResult<()> {
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        let mut bundle = MemoryBundle::new();
        let statuses = bundle.initialize(py)?;
        for (layer, status) in statuses.iter() {
            println!("{}: {}", layer, status);
        }
        Ok(())
    })
}
