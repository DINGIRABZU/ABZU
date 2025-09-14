// Patent pending – see PATENTS.md
//! Insight reasoning routines for NeoABZU.

use std::collections::HashMap;

use pyo3::prelude::*;

/// Generate basic insights by counting word frequencies within `text`.
pub fn analyze(text: &str) -> Vec<(String, usize)> {
    let mut counts: HashMap<String, usize> = HashMap::new();
    for word in text.split_whitespace() {
        let key = word.to_lowercase();
        *counts.entry(key).or_insert(0) += 1;
    }
    let mut pairs: Vec<(String, usize)> = counts.into_iter().collect();
    pairs.sort_by(|a, b| b.1.cmp(&a.1));
    pairs
}

#[pyfunction]
fn reason(text: &str) -> PyResult<Vec<(String, usize)>> {
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
    fn test_analyze_counts_words() {
        let res = analyze("hi hi there");
        assert_eq!(res[0], ("hi".to_string(), 2));
        assert!(res.iter().any(|(w, c)| w == "there" && *c == 1));
    }
}
