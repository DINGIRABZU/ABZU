use neoabzu_core::reduce_inevitable_with_journey;
use neoabzu_narrative::journey::HeroStage;

#[test]
fn hero_journey_traverses_all_stages() {
    let (i, journey) = reduce_inevitable_with_journey("(♀ :: ∞) :: ∅");
    assert!((i - 1.0).abs() < f32::EPSILON);
    assert_eq!(journey.len(), 12);
    assert_eq!(journey.first(), Some(&HeroStage::OrdinaryWorld));
    assert_eq!(journey.last(), Some(&HeroStage::ReturnWithTheElixir));
}
