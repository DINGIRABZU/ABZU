use neoabzu_crown::{insight_embedding, insight_semantic};

#[test]
fn exposes_insight_hooks() {
    let emb = insight_embedding("hello world").unwrap();
    assert_eq!(emb.len(), 3);
    let sims = insight_semantic("hello world").unwrap();
    assert_eq!(sims.len(), 2);
}
