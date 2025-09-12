//! Lightweight vector search module.
//!
//! Enable telemetry with:
//! `cargo test -p neoabzu-vector --features opentelemetry`
use pyo3::prelude::*;

#[cfg_attr(feature = "tracing", tracing::instrument)]
#[pyfunction]
fn search(text: &str, top_n: usize) -> PyResult<Vec<(String, f32)>> {
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

    #[test]
    fn returns_requested_count() {
        let res = search("a", 2).unwrap();
        assert_eq!(res.len(), 2);
        assert_eq!(res[0].0, "a0");
    }
}
