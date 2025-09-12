// Patent pending – see PATENTS.md
use pyo3::prelude::*;
use serde::Deserialize;

#[derive(Deserialize)]
struct Concept {
    symbol: Option<String>,
    glyph: Option<String>,
    inevitability_gradient: f32,
}

#[derive(Deserialize)]
struct Lexicon {
    concepts: Vec<Concept>,
}

fn lookup_gradient(symbol: &str, lexicon: &Lexicon) -> Option<f32> {
    for c in &lexicon.concepts {
        if c.symbol.as_deref() == Some(symbol) || c.glyph.as_deref() == Some(symbol) {
            return Some(c.inevitability_gradient);
        }
    }
    None
}

/// Reduce a ceremonial expression into its inevitability gradient.
pub fn reduce_inevitable(expr: &str) -> f32 {
    let lexicon: Lexicon =
        ron::from_str(include_str!("../resources/lexicon.ron")).expect("invalid lexicon");
    let cleaned = expr.replace(['(', ')', ' '], "");
    let tokens: Vec<&str> = cleaned.split("::").filter(|s| !s.is_empty()).collect();
    let mut current = 0.0;
    for token in tokens {
        if let Some(g) = lookup_gradient(token, &lexicon) {
            if g > current {
                current = g;
            }
        }
    }
    current
}

#[pyfunction]
#[pyo3(name = "reduce_inevitable")]
pub(crate) fn reduce_inevitable_py(expr: &str) -> PyResult<f32> {
    Ok(reduce_inevitable(expr))
}
