// Patent pending – see PATENTS.md
//! Insight reasoning routines for NeoABZU.

use std::collections::HashMap;

use pyo3::prelude::*;

/// Generate insights by counting word and bigram frequencies within `text`.
pub fn analyze(text: &str) -> HashMap<String, Vec<(String, usize)>> {
    let words: Vec<&str> = text.split_whitespace().collect();
    let mut word_counts: HashMap<String, usize> = HashMap::new();
    let mut bigram_counts: HashMap<String, usize> = HashMap::new();

    for window in words.windows(2) {
        let bigram = format!("{} {}", window[0].to_lowercase(), window[1].to_lowercase());
        *bigram_counts.entry(bigram).or_insert(0) += 1;
    }

    for w in &words {
        let key = w.to_lowercase();
        *word_counts.entry(key).or_insert(0) += 1;
    }

    let mut word_pairs: Vec<(String, usize)> = word_counts.into_iter().collect();
    word_pairs.sort_by(|a, b| b.1.cmp(&a.1));

    let mut bigram_pairs: Vec<(String, usize)> = bigram_counts.into_iter().collect();
    bigram_pairs.sort_by(|a, b| b.1.cmp(&a.1));

    let mut report = HashMap::new();
    report.insert("words".to_string(), word_pairs);
    report.insert("bigrams".to_string(), bigram_pairs);
    report
}

#[pyfunction]
fn reason(text: &str) -> PyResult<HashMap<String, Vec<(String, usize)>>> {
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
    fn test_analyze_counts_words_and_bigrams() {
        let report = analyze("hi there hi");
        assert_eq!(report["words"][0], ("hi".to_string(), 2));
        assert!(report["bigrams"].iter().any(|(b, c)| b == "hi there" && *c == 1));
    }
}
