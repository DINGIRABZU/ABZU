// Patent pending – see PATENTS.md
//! Insight reasoning routines for NeoABZU.

use pyo3::prelude::*;

/// Reverse the provided text to simulate insight generation.
pub fn analyze(text: &str) -> String {
    text.chars().rev().collect()
}

#[pyfunction]
fn reason(text: &str) -> PyResult<String> {
    Ok(analyze(text))
}

#[pymodule]
fn neoabzu_insight(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(reason, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_analyze_reverses_text() {
        assert_eq!(analyze("abc"), "cba");
    }
}
