use neoabzu_insight::{analyze, embedding, semantics};

#[test]
fn handles_empty_input() {
    let report = analyze("");
    assert!(report["words"].is_empty());
    let emb = embedding("");
    assert_eq!(emb, vec![0.0, 0.0, 0.0]);
    let sims = semantics("");
    assert!(sims.is_empty());
}
