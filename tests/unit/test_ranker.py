"""Unit tests for pathway ranking models."""
import pytest

from ace.domain.learner import LearnerProfile, LearningPreferences, PacePreference
from ace.domain.learning_path import LearningPath, LearningStep
from ace.ranking.ranker import HybridRanker, LinearRankingModel, RuleBasedRanker


def create_dummy_path(strategy: str, composite: float, goal: float, smooth: float) -> LearningPath:
    step = LearningStep(
        order=1,
        skill_id="s1",
        skill_name="S1",
        category="General",
        estimated_hours=10,
        rationale="Start",
        prerequisites_satisfied=[],
    )
    return LearningPath(
        learner_id="l1",
        career_id="c1",
        career_name="C1",
        total_skills=1,
        total_estimated_hours=10,
        steps=[step],
        strategy=strategy,
        composite_score=composite,
        objective_scores={"goal_alignment": goal, "difficulty_smoothness": smooth},
    )


@pytest.mark.unit
def test_rule_based_ranker_sorts_by_composite_score():
    ranker = RuleBasedRanker()
    p1 = create_dummy_path("PathLow", 0.65, 0.6, 0.7)
    p2 = create_dummy_path("PathHigh", 0.88, 0.9, 0.85)

    ranked = ranker.rank_paths([p1, p2], LearnerProfile(id="l1"))
    assert ranked[0].strategy == "PathHigh"
    assert ranked[1].strategy == "PathLow"


@pytest.mark.unit
def test_linear_ranking_model_preference_adaptation():
    learner = LearnerProfile(
        id="l_fast",
        preferences=LearningPreferences(pace_preference=PacePreference.FAST_TRACK),
    )
    model = LinearRankingModel()

    # Path A has high goal alignment, Path B has high smoothness
    path_a = create_dummy_path("HighGoal", 0.75, goal=0.95, smooth=0.40)
    path_b = create_dummy_path("HighSmooth", 0.75, goal=0.40, smooth=0.95)

    ranked = model.rank_paths([path_b, path_a], learner)
    # Fast track preference prioritizes high goal alignment
    assert ranked[0].strategy == "HighGoal"


@pytest.mark.unit
def test_hybrid_ranker():
    hybrid = HybridRanker()
    p1 = create_dummy_path("PathA", 0.80, 0.8, 0.8)
    ranked = hybrid.rank_paths([p1], LearnerProfile(id="l1"))
    assert len(ranked) == 1
    assert ranked[0].strategy == "PathA"
