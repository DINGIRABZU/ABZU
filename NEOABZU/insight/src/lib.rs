// Patent pending – see PATENTS.md
//! Insight reasoning routines for NeoABZU.

use std::collections::HashMap;

use pyo3::prelude::*;

/// Simple character-based embedding for a single word.
fn word_embedding(word: &str) -> Vec<f32> {
    let mut vowels = 0_f32;
    let mut consonants = 0_f32;
    for ch in word.chars() {
        if ch.is_ascii_alphabetic() {
            match ch.to_ascii_lowercase() {
                'a' | 'e' | 'i' | 'o' | 'u' => vowels += 1.0,
                _ => consonants += 1.0,
            }
        }
    }
    vec![vowels, consonants, word.len() as f32]
}

/// Generate simple embeddings for words and bigrams within `text`.
pub fn analyze(text: &str) -> HashMap<String, Vec<(String, Vec<f32>)>> {
    let words: Vec<&str> = text.split_whitespace().collect();
    let mut word_embeddings: Vec<(String, Vec<f32>)> = Vec::new();
    let mut bigram_embeddings: Vec<(String, Vec<f32>)> = Vec::new();

    for w in &words {
        word_embeddings.push(((*w).to_string(), word_embedding(w)));
    }

    for window in words.windows(2) {
        let bigram = format!("{} {}", window[0], window[1]);
        let e1 = word_embedding(window[0]);
        let e2 = word_embedding(window[1]);
        let avg: Vec<f32> = e1.iter().zip(e2.iter()).map(|(a, b)| (a + b) / 2.0).collect();
        bigram_embeddings.push((bigram, avg));
    }

    let mut report = HashMap::new();
    report.insert("words".to_string(), word_embeddings);
    report.insert("bigrams".to_string(), bigram_embeddings);
    report
}

/// Average embedding for the entire `text`.
pub fn embedding(text: &str) -> Vec<f32> {
    let report = analyze(text);
    let words = report.get("words").cloned().unwrap_or_default();
    if words.is_empty() {
        return vec![0.0, 0.0, 0.0];
    }
    let count = words.len() as f32;
    let mut sum = vec![0.0, 0.0, 0.0];
    for (_, emb) in &words {
        for (i, v) in emb.iter().enumerate() {
            sum[i] += v;
        }
    }
    sum.iter().map(|v| v / count).collect()
}

#[pyfunction]
fn reason(text: &str) -> PyResult<HashMap<String, Vec<(String, Vec<f32>)>>> {
    Ok(analyze(text))
}

#[pyfunction]
fn embed(text: &str) -> PyResult<Vec<f32>> {
    Ok(embedding(text))
}

#[pymodule]
fn neoabzu_insight(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(reason, m)?)?;
    m.add_function(wrap_pyfunction!(embed, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_analyze_embeds_words_and_bigrams() {
        let report = analyze("hi there");
        assert_eq!(report["words"][0].0, "hi");
        assert_eq!(report["words"][0].1.len(), 3);
        assert_eq!(report["bigrams"][0].0, "hi there");
    }

    #[test]
    fn test_embedding_average_dimensions() {
        let emb = embedding("hi there");
        assert_eq!(emb.len(), 3);
        assert!(emb.iter().all(|v| *v >= 0.0));
    }
}
