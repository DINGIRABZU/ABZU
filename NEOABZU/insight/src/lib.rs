// Patent pending – see PATENTS.md
//! Insight reasoning routines for NeoABZU.

use std::collections::HashMap;
use std::time::Instant;

use metrics::{counter, histogram};
use pyo3::prelude::*;
#[cfg(feature = "tracing")]
use tracing::instrument;

type Report = HashMap<String, Vec<(String, Vec<f32>)>>;

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
#[cfg_attr(feature = "tracing", instrument)]
pub fn analyze(text: &str) -> Report {
    let start = Instant::now();
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
        let avg: Vec<f32> = e1
            .iter()
            .zip(e2.iter())
            .map(|(a, b)| (a + b) / 2.0)
            .collect();
        bigram_embeddings.push((bigram, avg));
    }

    let mut report = HashMap::new();
    report.insert("words".to_string(), word_embeddings);
    report.insert("bigrams".to_string(), bigram_embeddings);
    counter!("neoabzu_insight_analyze_total", 1);
    histogram!(
        "neoabzu_insight_analyze_latency_seconds",
        start.elapsed().as_secs_f64()
    );
    report
}

/// Average embedding for the entire `text`.
#[cfg_attr(feature = "tracing", instrument)]
pub fn embedding(text: &str) -> Vec<f32> {
    let start = Instant::now();
    let report = analyze(text);
    let words = report.get("words").cloned().unwrap_or_default();
    if words.is_empty() {
        return vec![0.0, 0.0, 0.0];
    }
    let count = words.len() as f32;
    let mut sum = [0.0_f32; 3];
    for (_, emb) in &words {
        for (i, v) in emb.iter().enumerate() {
            sum[i] += v;
        }
    }
    let emb: Vec<f32> = sum.iter().map(|v| v / count).collect();
    counter!("neoabzu_insight_embedding_total", 1);
    histogram!(
        "neoabzu_insight_embedding_latency_seconds",
        start.elapsed().as_secs_f64()
    );
    emb
}

/// Cosine similarity between two vectors.
fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|v| v * v).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|v| v * v).sum::<f32>().sqrt();
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

/// Semantic similarity scores for each word against the overall text embedding.
#[cfg_attr(feature = "tracing", instrument)]
pub fn semantics(text: &str) -> Vec<(String, f32)> {
    let start = Instant::now();
    let doc_emb = embedding(text);
    if doc_emb.iter().all(|v| *v == 0.0) {
        return Vec::new();
    }
    let report = analyze(text);
    let words = report.get("words").cloned().unwrap_or_default();
    let out: Vec<(String, f32)> = words
        .into_iter()
        .map(|(w, emb)| {
            let sim = cosine_similarity(&emb, &doc_emb);
            (w, sim)
        })
        .collect();
    counter!("neoabzu_insight_semantics_total", 1);
    histogram!(
        "neoabzu_insight_semantics_latency_seconds",
        start.elapsed().as_secs_f64()
    );
    out
}

#[pyfunction]
fn reason(text: &str) -> PyResult<Report> {
    Ok(analyze(text))
}

#[pyfunction]
fn embed(text: &str) -> PyResult<Vec<f32>> {
    Ok(embedding(text))
}

#[pyfunction]
fn semantic(text: &str) -> PyResult<Vec<(String, f32)>> {
    Ok(semantics(text))
}

#[pymodule]
fn neoabzu_insight(_py: Python<'_>, m: &Bound<PyModule>) -> PyResult<()> {
    #[cfg(feature = "tracing")]
    let _ = neoabzu_instrumentation::init_tracing("insight");
    m.add_function(wrap_pyfunction!(reason, m)?)?;
    m.add_function(wrap_pyfunction!(embed, m)?)?;
    m.add_function(wrap_pyfunction!(semantic, m)?)?;
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

    #[test]
    fn test_semantics_scores_words() {
        let sims = semantics("hi there");
        assert_eq!(sims.len(), 2);
        assert!(sims.iter().all(|(_, s)| *s >= 0.0));
    }
}
