//! Narrative reduction utilities with Sumerian phoneme embedding.

pub mod journey;

use std::collections::HashMap;

#[cfg(feature = "tracing")]
use tracing::info;

/// Generate progressive reductions of the input text by
/// removing one word at a time from the end.
pub fn reduction_steps(text: &str) -> Vec<String> {
    let mut words: Vec<&str> = text.split_whitespace().collect();
    let mut steps = Vec::new();
    while !words.is_empty() {
        let current = words.join(" ");
        #[cfg(feature = "tracing")]
        info!(step = steps.len() + 1, current);
        steps.push(current);
        words.pop();
    }
    steps
}

/// Embed Sumerian phonemes for characters in the text.
pub fn embed_sumerian_phonemes(text: &str) -> Vec<&'static str> {
    let map = phoneme_map();
    let mut out = Vec::new();
    for ch in text.to_lowercase().chars() {
        if let Some(&phoneme) = map.get(&ch) {
            #[cfg(feature = "tracing")]
            info!(phoneme, grapheme = %ch);
            out.push(phoneme);
        }
    }
    out
}

fn phoneme_map() -> HashMap<char, &'static str> {
    let pairs = [
        ('a', "a"),
        ('e', "e"),
        ('i', "i"),
        ('u', "u"),
        ('b', "ba"),
        ('d', "da"),
        ('g', "ga"),
        ('k', "ka"),
        ('l', "la"),
        ('m', "ma"),
        ('n', "na"),
        ('p', "pa"),
        ('r', "ra"),
        ('s', "sa"),
        ('t', "ta"),
    ];
    pairs.into_iter().collect()
}

/// Evaluate a narrative by capturing its reduction steps and
/// embedding Sumerian phonemes. Each evaluation emits tracing logs
/// when the `tracing` feature is enabled.
pub fn evaluate(text: &str) -> (Vec<String>, Vec<&'static str>) {
    #[cfg(feature = "tracing")]
    info!("narrative.evaluate.start");
    let steps = reduction_steps(text);
    let phonemes = embed_sumerian_phonemes(text);
    #[cfg(feature = "tracing")]
    info!(
        steps = steps.len(),
        phonemes = phonemes.len(),
        "narrative.evaluate.complete"
    );
    (steps, phonemes)
}

#[cfg(test)]
mod tests {
    use super::{embed_sumerian_phonemes, evaluate, reduction_steps};

    #[test]
    fn reductions_progressively_trim_text() {
        let text = "ba da";
        let steps = reduction_steps(text);
        assert_eq!(steps, vec!["ba da", "ba"]);
    }

    #[test]
    fn embeddings_map_letters_to_phonemes() {
        let text = "bad";
        let phonemes = embed_sumerian_phonemes(text);
        assert_eq!(phonemes, vec!["ba", "a", "da"]);
    }

    #[test]
    fn evaluate_combines_steps_and_phonemes() {
        let text = "ba";
        let (steps, phonemes) = evaluate(text);
        assert_eq!(steps, vec!["ba"]);
        assert_eq!(phonemes, vec!["ba", "a"]);
    }
}
