"""Unit tests for structured reason codes and curriculum explainers."""
import networkx as nx
import pytest

from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learning_path import LearningPath
from ace.explain.structured_rationale import generate_deterministic_explanation, populate_step_rationales
from ace.infrastructure.llm.client import MockLLMProvider
from ace.infrastructure.llm.explainer import CurriculumExplainer


@pytest.fixture
def explanation_graph_and_career():
    graph = nx.DiGraph()
    graph.add_node("html", name="HTML Basics", category="Frontend", estimated_hours=10, difficulty=1)
    graph.add_node("css", name="CSS Styling", category="Frontend", estimated_hours=15, difficulty=2)
    graph.add_node("js", name="JavaScript", category="Frontend", estimated_hours=30, difficulty=3)
    graph.add_edges_from([("html", "css"), ("css", "js")])

    career = Career(
        id="fe",
        name="Frontend Engineer",
        required_skills=[
            CareerSkillRequirement(skill_id="html", is_mandatory=True, importance=5),
            CareerSkillRequirement(skill_id="css", is_mandatory=True, importance=4),
            CareerSkillRequirement(skill_id="js", is_mandatory=True, importance=5),
        ],
    )
    return graph, career


@pytest.mark.unit
def test_populate_step_rationales_assigns_reason_codes(explanation_graph_and_career):
    graph, career = explanation_graph_and_career
    steps = populate_step_rationales(
        path_skill_ids=["html", "css", "js"],
        graph=graph,
        career=career,
    )

    assert len(steps) == 3

    # Step 1: HTML
    assert steps[0].order == 1
    assert "FOUNDATION_START" in steps[0].reason_codes
    assert "NO_PREREQUISITES" in steps[0].reason_codes
    assert "QUICK_WIN" in steps[0].reason_codes

    # Step 2: CSS
    assert "PREREQUISITE_CLEARED" in steps[1].reason_codes
    assert "CATEGORY_CONTINUITY" in steps[1].reason_codes

    # Step 3: JS
    assert "PREREQUISITE_CLEARED" in steps[2].reason_codes
    assert "CAREER_MANDATORY" in steps[2].reason_codes


@pytest.mark.unit
def test_deterministic_explanation_markdown(explanation_graph_and_career):
    graph, career = explanation_graph_and_career
    steps = populate_step_rationales(["html", "css", "js"], graph, career)

    path = LearningPath(
        learner_id="test_learner",
        career_id=career.id,
        career_name=career.name,
        total_skills=3,
        total_estimated_hours=55,
        steps=steps,
        strategy="foundational_first",
        objective_scores={"goal_alignment": 0.88, "difficulty_smoothness": 0.92},
    )

    markdown = generate_deterministic_explanation(path)
    assert "## Personalized Curriculum Roadmap" in markdown
    assert "HTML Basics" in markdown
    assert "Pedagogical Quality Profile" in markdown


@pytest.mark.unit
def test_curriculum_explainer_with_mock_provider(explanation_graph_and_career):
    graph, career = explanation_graph_and_career
    steps = populate_step_rationales(["html", "css"], graph, career)
    path = LearningPath(
        learner_id="l1",
        career_id=career.id,
        career_name=career.name,
        total_skills=2,
        total_estimated_hours=25,
        steps=steps,
        strategy="quick_wins",
    )

    explainer = CurriculumExplainer(provider=MockLLMProvider())
    explanation = explainer.explain_path(path)
    assert len(explanation) > 0
    assert "HTML Basics" in explanation
