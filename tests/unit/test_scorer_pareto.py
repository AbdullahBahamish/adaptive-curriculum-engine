"""Unit tests for MultiObjectivePathScorer and ParetoOptimizer."""
import networkx as nx
import pytest

from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learner import LearnerProfile, LearningPreferences, PacePreference
from ace.planner.pareto import ParetoCandidate, ParetoOptimizer
from ace.planner.scorer import MultiObjectivePathScorer, PathwayObjectiveScores


@pytest.fixture
def mock_subgraph_and_career():
    graph = nx.DiGraph()
    graph.add_node("s1", difficulty=1, estimated_hours=10, category="Foundations")
    graph.add_node("s2", difficulty=2, estimated_hours=20, category="Core")
    graph.add_node("s3", difficulty=3, estimated_hours=30, category="Core")
    graph.add_edges_from([("s1", "s2"), ("s2", "s3")])

    career = Career(
        id="c1",
        name="Career 1",
        required_skills=[
            CareerSkillRequirement(skill_id="s1", importance=5),
            CareerSkillRequirement(skill_id="s2", importance=4),
            CareerSkillRequirement(skill_id="s3", importance=3),
        ],
    )
    learner = LearnerProfile(id="l1", preferences=LearningPreferences(weekly_hours_budget=15))
    return graph, career, learner


@pytest.mark.unit
def test_scorer_objective_bounds(mock_subgraph_and_career):
    graph, career, learner = mock_subgraph_and_career
    scorer = MultiObjectivePathScorer(career=career, learner=learner, subgraph=graph)

    scores = scorer.score_path(["s1", "s2", "s3"])
    assert 0.0 <= scores.goal_alignment <= 1.0
    assert 0.0 <= scores.gap_reduction <= 1.0
    assert 0.0 <= scores.difficulty_smoothness <= 1.0
    assert 0.0 <= scores.time_budget_fit <= 1.0
    assert 0.0 <= scores.category_continuity <= 1.0
    assert 0.0 <= scores.composite_score <= 1.0


@pytest.mark.unit
def test_scorer_pacing_weight_adjustment(mock_subgraph_and_career):
    graph, career, _ = mock_subgraph_and_career
    learner_fast = LearnerProfile(
        id="l_fast",
        preferences=LearningPreferences(pace_preference=PacePreference.FAST_TRACK),
    )
    learner_found = LearnerProfile(
        id="l_found",
        preferences=LearningPreferences(pace_preference=PacePreference.FOUNDATIONAL_FIRST),
    )

    scorer_fast = MultiObjectivePathScorer(career=career, learner=learner_fast, subgraph=graph)
    scorer_found = MultiObjectivePathScorer(career=career, learner=learner_found, subgraph=graph)

    w_fast = scorer_fast._get_weights()
    w_found = scorer_found._get_weights()

    assert w_fast["goal"] > w_found["goal"]
    assert w_found["smooth"] > w_fast["smooth"]


@pytest.mark.unit
def test_pareto_dominance_and_frontier():
    optimizer = ParetoOptimizer()

    cand_a = ParetoCandidate(
        strategy="A",
        skill_ids=["1", "2"],
        scores=PathwayObjectiveScores(0.9, 0.9, 0.9, 0.9, 0.9, 0.9),
    )
    cand_b = ParetoCandidate(
        strategy="B",
        skill_ids=["2", "1"],
        scores=PathwayObjectiveScores(0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
    )
    cand_c = ParetoCandidate(
        strategy="C",
        skill_ids=["1", "2"],
        scores=PathwayObjectiveScores(0.4, 0.95, 0.95, 0.9, 0.9, 0.8),
    )

    # A strictly dominates B
    assert optimizer.dominates(cand_a.scores, cand_b.scores)
    # A does not dominate C (C has higher gap_reduction 0.95 > 0.9)
    assert not optimizer.dominates(cand_a.scores, cand_c.scores)

    frontier = optimizer.extract_frontier([cand_a, cand_b, cand_c])
    frontier_strategies = {c.strategy for c in frontier}
    assert "A" in frontier_strategies
    assert "C" in frontier_strategies
    assert "B" not in frontier_strategies


@pytest.mark.unit
def test_pareto_tradeoffs_explanation():
    optimizer = ParetoOptimizer()
    rec = ParetoCandidate("GoalFirst", ["a", "b"], PathwayObjectiveScores(0.95, 0.8, 0.6, 0.9, 0.5, 0.82))
    alt = ParetoCandidate("Foundational", ["b", "a"], PathwayObjectiveScores(0.70, 0.8, 0.95, 0.9, 0.8, 0.80))

    tradeoffs = optimizer.explain_tradeoffs(recommended=rec, alternatives=[alt])
    assert len(tradeoffs) == 2
    rec_to = tradeoffs[0]
    alt_to = tradeoffs[1]

    assert rec_to.is_recommended is True
    assert alt_to.is_recommended is False
    assert any("smoother cognitive difficulty gradient" in t for t in alt_to.tradeoffs_vs_primary)
