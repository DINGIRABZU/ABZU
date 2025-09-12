use neoabzu_core::reduce_inevitable;

#[test]
fn first_ceremony_alignment() {
    let i = reduce_inevitable("(♀ :: ∞) :: ∅");
    assert!((i - 1.0).abs() < f32::EPSILON);
}
