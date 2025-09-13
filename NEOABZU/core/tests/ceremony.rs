use neoabzu_core::reduce_inevitable_with_journey;

#[test]
fn ceremony_narrative_logged() {
    let (i, journey) = reduce_inevitable_with_journey("(♀ :: ∞) :: ∅");
    assert!((i - 1.0).abs() < f32::EPSILON);
    let narrative = journey
        .iter()
        .map(|s| format!("{:?}", s))
        .collect::<Vec<_>>()
        .join(" -> ");
    println!("ceremony_journey: {narrative}");
}
