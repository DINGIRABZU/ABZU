use neoabzu_insight::{analyze, embedding, semantics};

#[test]
fn embeds_tokens() {
    let report = analyze("one two");
    assert_eq!(report["words"][0].0, "one");
    assert_eq!(report["bigrams"][0].0, "one two");
    let emb = embedding("one two");
    assert_eq!(emb.len(), 3);
    let sims = semantics("one two");
    assert_eq!(sims.len(), 2);
}
