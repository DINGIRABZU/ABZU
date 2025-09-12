use core::cmp::min;

/// Stages of the hero's journey as encoded by the narrative engine.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HeroStage {
    OrdinaryWorld,
    CallToAdventure,
    RefusalOfTheCall,
    MeetingTheMentor,
    CrossingTheThreshold,
    TestsAlliesEnemies,
    ApproachToTheInmostCave,
    Ordeal,
    Reward,
    RoadBack,
    Resurrection,
    ReturnWithTheElixir,
}

/// Compute the hero stage for a given reduction step.
///
/// `step` is the zero-based index of the current step and `total`
/// is the total number of reduction steps to perform.
pub fn stage_for_step(step: usize, total: usize) -> HeroStage {
    const STAGES: [HeroStage; 12] = [
        HeroStage::OrdinaryWorld,
        HeroStage::CallToAdventure,
        HeroStage::RefusalOfTheCall,
        HeroStage::MeetingTheMentor,
        HeroStage::CrossingTheThreshold,
        HeroStage::TestsAlliesEnemies,
        HeroStage::ApproachToTheInmostCave,
        HeroStage::Ordeal,
        HeroStage::Reward,
        HeroStage::RoadBack,
        HeroStage::Resurrection,
        HeroStage::ReturnWithTheElixir,
    ];
    if total == 0 {
        return HeroStage::OrdinaryWorld;
    }
    let idx = step * (STAGES.len() - 1) / total;
    STAGES[min(idx, STAGES.len() - 1)]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn maps_first_and_last_steps() {
        let total = 5;
        assert_eq!(stage_for_step(0, total), HeroStage::OrdinaryWorld);
        assert_eq!(stage_for_step(total, total), HeroStage::ReturnWithTheElixir);
    }
}
