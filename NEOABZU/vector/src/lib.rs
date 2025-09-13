//! Lightweight vector search module.
//!
//! Enable telemetry with:
//! `cargo test -p neoabzu-vector --features opentelemetry`
use pyo3::prelude::*;

#[cfg_attr(feature = "tracing", tracing::instrument(skip(py)))]
#[pyfunction]
fn search(py: Python<'_>, text: &str, top_n: usize) -> PyResult<Vec<(String, f32)>> {
    let _ = py;
    let results = (0..top_n)
        .map(|i| (format!("{text}{i}"), 1.0))
        .collect();
    Ok(results)
}

#[pymodule]
fn neoabzu_vector(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::search;
    use pyo3::prelude::*;

    #[test]
    fn returns_requested_count() {
        Python::with_gil(|py| {
            let res = search(py, "a", 2).unwrap();
            assert_eq!(res.len(), 2);
            assert_eq!(res[0].0, "a0");
        });
    }
}
