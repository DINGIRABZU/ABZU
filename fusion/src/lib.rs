/// Types representing invariants and inevitability gradients.
pub type Invariant = String;
pub type InevitabilityGradient = f64;

/// Accepts `(Invariant, InevitabilityGradient)` pairs from both
/// symbolic and numeric realms and merges them into a unified
/// collection.
pub fn accept_pairs(
    symbolic: Vec<(Invariant, InevitabilityGradient)>,
    numeric: Vec<(Invariant, InevitabilityGradient)>,
) -> Vec<(Invariant, InevitabilityGradient)> {
    symbolic.into_iter().chain(numeric).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn merges_pairs_from_both_realms() {
        let sym = vec![("sym".to_string(), 1.0)];
        let num = vec![("num".to_string(), 2.0)];
        let fused = accept_pairs(sym, num);
        assert_eq!(fused.len(), 2);
    }
}
