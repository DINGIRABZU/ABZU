use neoabzu_insight::analyze;

#[test]
fn counts_bigrams() {
    let report = analyze("one two one");
    assert_eq!(report["words"][0], ("one".to_string(), 2));
    assert!(report["bigrams"].iter().any(|(b, c)| b == "one two" && *c == 1));
}
