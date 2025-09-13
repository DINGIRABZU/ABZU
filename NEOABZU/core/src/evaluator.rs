// Patent pending – see PATENTS.md
use pyo3::prelude::*;
use serde::Deserialize;

use neoabzu_narrative::journey::{stage_for_step, HeroStage};
#[cfg(feature = "tracing")]
use tracing::info;

#[derive(Deserialize)]
struct Concept {
    #[serde(default)]
    symbol: String,
    #[serde(default)]
    glyph: String,
    #[serde(default)]
    phonetic: String,
    inevitability_gradient: f32,
}

#[derive(Deserialize)]
struct Lexicon {
    concepts: Vec<Concept>,
}

fn lookup_gradient(symbol: &str, lexicon: &Lexicon) -> Option<f32> {
    for c in &lexicon.concepts {
        if c.symbol == symbol || c.glyph == symbol {
            return Some(c.inevitability_gradient);
        }
    }
    None
}

/// Reduce a ceremonial expression into its inevitability gradient while recording the hero's journey.
pub fn reduce_inevitable_with_journey(expr: &str) -> (f32, Vec<HeroStage>) {
    let lexicon: Lexicon =
        ron::from_str(include_str!("../resources/lexicon.ron")).expect("invalid lexicon");
    let cleaned = expr.replace(['(', ')', ' '], "");
    let tokens: Vec<&str> = cleaned.split("::").filter(|s| !s.is_empty()).collect();
    const TOTAL_STEPS: usize = 11;
    let mut current = 0.0;
    let mut journey = Vec::new();
    for step in 0..=TOTAL_STEPS {
        let stage = stage_for_step(step, TOTAL_STEPS);
        let token = tokens[step % tokens.len()];
        #[cfg(feature = "tracing")]
        info!(stage = ?stage, token, "hero_journey.stage");
        if let Some(g) = lookup_gradient(token, &lexicon) {
            if g > current {
                current = g;
            }
        }
        journey.push(stage);
    }
    (current, journey)
}

/// Reduce a ceremonial expression into its inevitability gradient.
pub fn reduce_inevitable(expr: &str) -> f32 {
    reduce_inevitable_with_journey(expr).0
}

#[pyfunction]
#[pyo3(name = "reduce_inevitable")]
pub(crate) fn reduce_inevitable_py(expr: &str) -> PyResult<(f32, Vec<String>)> {
    let (i, journey) = reduce_inevitable_with_journey(expr);
    let stages = journey.iter().map(|s| format!("{:?}", s)).collect();
    Ok((i, stages))
}
