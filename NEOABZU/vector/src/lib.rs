use pyo3::prelude::*;

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
